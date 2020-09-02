from starry_process.latitude import LatitudeIntegral
from starry_process.ops import LatitudeIntegralOp
from starry_process.wigner import R
import numpy as np
from scipy.integrate import quad
from scipy.stats import beta as Beta
from tqdm import tqdm
from theano.tests.unittest_tools import verify_grad
from theano.configparser import change_flags


def test_latitude(
    ydeg=3, alpha=10.0, beta=30.0, rtol=1e-12, ftol=1e-10, **kwargs
):

    # Random input moment matrices
    np.random.seed(0)
    N = (ydeg + 1) ** 2
    s = np.random.randn(N)
    eigS = np.random.randn(N, N) / N
    S = eigS @ eigS.T

    # Get analytic integrals
    print("Computing moments analytically...")
    I = LatitudeIntegral(ydeg=ydeg, **kwargs)
    I._set_params(alpha, beta)
    e = I._first_moment(s).eval()
    eigE = I._second_moment(eigS).eval()
    E = eigE @ eigE.T

    # Get the first moment by numerical integration
    e_num = np.zeros(N)
    print("Computing first moment numerically...")
    for n in tqdm(range(N)):

        def func(phi):
            Rl = R(
                ydeg,
                phi=phi,
                cos_alpha=0,
                sin_alpha=1,
                cos_gamma=0,
                sin_gamma=-1,
            )
            Rs = np.zeros(N)
            for l in range(ydeg + 1):
                i = slice(l ** 2, (l + 1) ** 2)
                Rs[i] = Rl[l] @ s[i]
            jac = 0.5 * np.abs(np.sin(phi))
            return Rs[n] * jac * Beta.pdf(np.cos(phi), alpha, beta)

        e_num[n] = quad(func, -np.pi, np.pi)[0]

    # Get the second moment by numerical integration
    E_num = np.zeros((N, N))
    print("Computing second moment numerically...")
    for n1 in tqdm(range(N)):
        for n2 in range(N):

            def func(phi):
                Rl = R(
                    ydeg,
                    phi=phi,
                    cos_alpha=0,
                    sin_alpha=1,
                    cos_gamma=0,
                    sin_gamma=-1,
                )
                RSRT = np.zeros((N, N))
                for l1 in range(ydeg + 1):
                    for l2 in range(ydeg + 1):
                        i = slice(l1 ** 2, (l1 + 1) ** 2)
                        j = slice(l2 ** 2, (l2 + 1) ** 2)
                        RSRT[i, j] = Rl[l1] @ S[i, j] @ Rl[l2].T

                jac = 0.5 * np.abs(np.sin(phi))
                return RSRT[n1, n2] * jac * Beta.pdf(np.cos(phi), alpha, beta)

            E_num[n1, n2] = quad(func, -np.pi, np.pi)[0]

    # Compare
    assert np.max(np.abs(e - e_num)) < rtol, "error in first moment"
    assert np.max(np.abs(1 - e / e_num)) < ftol, "error in first moment"
    assert np.max(np.abs(E - E_num)) < rtol, "error in second moment"
    assert np.max(np.abs(1 - E / E_num)) < ftol, "error in second moment"


def test_latitude_grad(
    ydeg=3, alpha=10.0, beta=30.0, abs_tol=1e-5, rel_tol=1e-5, eps=1e-7
):
    with change_flags(compute_test_value="off"):
        op = LatitudeIntegralOp(ydeg)

        # d/dq
        verify_grad(
            lambda alpha, beta: op(alpha, beta)[0],
            (alpha, beta,),
            n_tests=1,
            abs_tol=abs_tol,
            rel_tol=rel_tol,
            eps=eps,
        )

        # d/dQ
        verify_grad(
            lambda alpha, beta: op(alpha, beta)[3],
            (alpha, beta,),
            n_tests=1,
            abs_tol=abs_tol,
            rel_tol=rel_tol,
            eps=eps,
        )