from .. import StarryProcess
from ..math import cho_factor, cho_solve
import numpy as np
import theano
import theano.tensor as tt
from theano.ifelse import ifelse


def get_log_prob(
    t,
    flux=None,
    ferr=1.0e-3,
    p=1.0,
    ydeg=15,
    baseline_var=1e-4,
    apply_jac=True,
    normalized=True,
    marginalize_over_inclination=True,
):

    # Dimensions
    K = len(t)

    # Set up the model
    r = tt.dscalar()
    a = tt.dscalar()
    b = tt.dscalar()
    c = tt.dscalar()
    n = tt.dscalar()
    i = tt.dscalar()
    if flux is None:
        free_flux = True
        flux = tt.dmatrix()
    else:
        free_flux = False
    sp = StarryProcess(
        ydeg=ydeg,
        r=r,
        a=a,
        b=b,
        c=c,
        n=n,
        marginalize_over_inclination=marginalize_over_inclination,
        covpts=len(t) - 1,
    )

    # Get # of light curves in batch
    flux = tt.as_tensor_variable(flux)
    nlc = tt.shape(flux)[0]

    # Compute the mean and covariance of the process
    gp_mean = sp.mean(t, p=p, i=i)
    gp_cov = sp.cov(t, p=p, i=i)

    if normalized:

        # Assume the data is normalized to zero mean.
        # We need to scale our covariance accordingly
        gp_cov /= (1 + gp_mean) ** 2
        R = tt.transpose(flux)

    else:

        # Assume we can measure the true baseline,
        # which is just the mean of the GP
        R = tt.transpose(flux) - tt.reshape(gp_mean, (-1, 1))

    # Observational error
    gp_cov += ferr ** 2 * tt.eye(K)

    # Marginalize over the baseline
    gp_cov += baseline_var

    # Compute the batched likelihood
    cho_gp_cov = cho_factor(gp_cov)
    CInvR = cho_solve(cho_gp_cov, R)
    log_like = -0.5 * tt.sum(
        tt.batched_dot(tt.transpose(R), tt.transpose(CInvR))
    )
    log_like -= nlc * tt.sum(tt.log(tt.diag(cho_gp_cov)))
    log_like -= 0.5 * nlc * K * tt.log(2 * np.pi)
    log_like = ifelse(tt.isnan(log_like), -np.inf, log_like)

    # Latitude jacobian
    if apply_jac:
        log_prob = log_like + sp.log_jac()
    else:
        log_prob = log_like

    # Free variables
    theano_vars = [r, a, b, c, n]
    if free_flux:
        theano_vars = [flux] + theano_vars
    if not marginalize_over_inclination:
        theano_vars = theano_vars + [i]

    # Compile & return
    log_prob = theano.function(theano_vars, log_prob)
    return log_prob
