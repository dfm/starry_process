from starry_process import StarryProcess
import numpy as np
import starry


def test_sample_conditional():

    # Sample the flux from the prior
    sp = StarryProcess()
    t = np.linspace(0, 2, 300)
    flux = sp.sample(t).eval().reshape(-1)

    # Now sample the ylms conditioned on the flux
    data_cov = 1e-12
    y = sp.sample_ylm_conditional(t, flux, data_cov).eval()
    map = starry.Map(15, inc=60, lazy=False)
    map[:, :] = y.reshape(-1)
    flux_pred = map.flux(theta=360 * t)

    # The computed flux should match the data pretty well
    assert np.sum((flux - flux_pred) ** 2) < 100 * data_cov