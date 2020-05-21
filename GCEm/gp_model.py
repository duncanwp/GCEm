import numpy as np
import tensorflow as tf
from .model import Model


class GPModel(Model):

    def train(self, X, params=None, verbose=False):
        with tf.device('/gpu:{}'.format(self._GPU)):
            import gpflow
            
            if params is None:
                n_params = X.shape[1]
                params = np.arange(n_params)
            else:
                n_params = len(params)
            
            if verbose:
                print("Fitting using dimensions: {}".format([params]))

            # Uses L-BFGS-B by default
            opt = gpflow.optimizers.Scipy()

            # TODO: A lot of this needs to be optional somehow
            k = gpflow.kernels.RBF(lengthscales=[0.5]*n_params, variance=0.01, active_dims=params) + \
                gpflow.kernels.Linear(variance=[1.]*n_params, active_dims=params) + \
                gpflow.kernels.Polynomial(variance=[1.]*n_params, active_dims=params) + \
                gpflow.kernels.Bias(active_dims=params)

            Y_flat = self.training_data.reshape((self.training_data.shape[0], -1))
            self.model = gpflow.models.GPR(data=(X, Y_flat), kernel=k)

            opt.minimize(self.model.training_loss,
                         variables=self.model.trainable_variables,
                         options=dict(disp=verbose, maxiter=100))
    
    def predict(self, *args, **kwargs):
        mean, var = self._tf_predict(*args, **kwargs)
        # Reshape the output to the original shape (neglecting the param dim)
        return (mean.numpy().reshape(self.original_shape[1:]),
                var.numpy().reshape(self.original_shape[1:]))

    def _post_process(self):
        pass

    def _tf_predict(self, *args, **kwargs):
        return self.model.predict_y(*args, **kwargs)

