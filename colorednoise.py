"""Generate colored noise."""

from numpy import sqrt
from numpy.fft import irfft, fftfreq
from numpy.random import normal


def powerlaw_psd_gaussian(exponent, size, fmin=0):
    """Gaussian (1/f)**beta noise.

    Based on the algorithm in:
    Timmer, J. and Koenig, M.:
    On generating power law noise.
    Astron. Astrophys. 300, 707-710 (1995)

    Normalised to unit variance

    Parameters:
    -----------

    exponent : float
        The power-spectrum of the generated noise is proportional to

        S(f) = (1 / f)**beta
        flicker / pink noise:   exponent beta = 1
        brown noise:            exponent beta = 2

        Furthermore, the autocorrelation decays proportional to lag**-gamma
        with gamma = 1 - beta for 0 < beta < 1.
        There may be finite-size issues for beta close to one.

    shape : int or iterable
        The output has the given shape, and the desired power spectrum in
        the last coordinate. That is, the last dimension is taken as time,
        and all other components are independent.

    fmin : float, optional
        Low-frequency cutoff.
        Default: 0 corresponds to original paper. It is not actually
        zero, but 1/samples.

    Returns
    -------
    out : array
        The samples.


    Examples:
    ---------

    # generate 1/f noise == pink noise == flicker noise
    >>> import colorednoise as cn
    >>> y = cn.powerlaw_psd_gaussian(1, 5)
    """

    # Make sure size is a list so we can iterate it and assign to it.
    try:
        size = list(size)
    except TypeError:
        size = [size]

    # The number of samples in each noise sequence.
    samples = size[-1]

    # frequencies (we asume a sample rate of one)
    f = fftfreq(samples)

    # scaling factor for all frequencies; calculate positive only
    s_scale = abs(f[:samples//2 + 1])
    s_scale[0] = 1/samples

    # Adjust the size so we only generate as many samples as needed.
    size[-1] = len(s_scale)

    # low frequency cutoff?!?
    if fmin:
        ix = sum(s_scale < fmin)
        if ix < len(s_scale):
            s_scale[:ix] = s_scale[ix]
    s_scale = s_scale**(-exponent/2.)

    # Change the shape of s_scale to broadcast correctly with
    # the generated random values, by generating enough new axes.
    dims_to_add = len(size) - 1
    s_scale = s_scale[(None,)*dims_to_add + (Ellipsis,)]

    # scale random power + phase
    sr = normal(size=size)
    si = normal(size=size)

    # If the signal length is even, this corresponds to frequency
    # +/- 0.5, so the coefficient must be real.
    if not (samples % 2): si[...,-1] = 0

    # Regardless of signal length, the DC component must be real.
    si[...,0] = 0

    # Use inverse real fft to automatically assume Hermitian
    # spectrum rather than constructing it ourselves.
    s = (sr + 1J * si)
    y = irfft(s * s_scale, n=samples, axis=-1)

    # Divide by theoretical standard deviation of each sequence
    # of noise values y, which should not be affected by any DC term.
    weights = s_scale
    weights[...,0] = 0
    weights[...,-1] *= (1 + (samples % 2)) / 2.
    weights = weights**2
    std = 2 * sqrt(weights.sum()) / samples
    return y / std
