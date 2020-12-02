from typing import Callable
import jax.numpy as jnp
import jax.random as jr
from .kernel import RBF
from jax import nn
from objax import TrainVar


# TODO: Create a base spectral class. Inherited kernels will then just need the sampling distribution altered.
class SpectralRBF(RBF):
    """
    Random Fourier feature approximation to the RBF kernel.
    """
    def __init__(self,
                 num_basis: int,
                 lengthscale: jnp.ndarray = jnp.array([1.]),
                 variance: jnp.ndarray = jnp.array([1.]),
                 parameter_transform: Callable = nn.softplus,
                 key=jr.PRNGKey(123),
                 name: str = "RBF"):
        super().__init__(parameter_transform=parameter_transform,
                         lengthscale=lengthscale,
                         variance=variance,
                         name=name)
        self.input_dim = lengthscale.shape[
            0]  # TODO: This assumes the lengthscale is ARD. This value should be driven by the data's dimension instead.
        self.num_basis = num_basis
        self.features = TrainVar(
            jr.normal(key, shape=(self.num_basis, self.input_dim)))
        self.spectral = True

    def _compute_phi(self, X: jnp.ndarray, scale=False):
        """
        Takes an NxD matrix and returns a 2*NxM matrix

        :param X:
        :return:
        """
        if scale:
            denom = self.lengthscale.value
        else:
            denom = jnp.ones_like(self.lengthscale.value)
        omega = self.features.value / denom
        cos_freqs = jnp.cos(X.dot(
            omega.T))  # TODO: Can possible do away with the tranpose
        sin_freqs = jnp.sin(X.dot(omega.T))
        phi = jnp.vstack((cos_freqs, sin_freqs))
        return phi

    def __call__(self, X: jnp.ndarray, Y: jnp.ndarray) -> jnp.ndarray:
        phi_matrix = self._compute_phi(X)
        return phi_matrix.dot(phi_matrix.T)
