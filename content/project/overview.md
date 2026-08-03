# EUVICS project overview

## EUVICS at a glance

EUVICS studies the design of a compact extreme ultraviolet (EUV) source based
on inverse Compton scattering (ICS). The project brings together an electron
accelerator, a synchronized laser, an interaction point, EUV collection optics,
diagnostics, and controls. Its present goal is to evaluate a design—not to claim
that a complete source has demonstrated a particular wavelength, photon yield,
bandwidth, brilliance, efficiency, stability, or readiness level.

[pyEUVICS](../software/science.md) is the reproducible calculation and
validation layer. This website explains the approved model boundary and links
to the package documentation; it does not maintain a separate implementation of
the physics.

## How inverse Compton scattering works

An incident laser photon collides with a relativistic electron. In a useful
two-Doppler-shift picture, the photon is blueshifted when transformed into the
electron rest frame, scatters there, and is boosted again when transformed back
to the laboratory frame. The most energetic scattered photons are concentrated
near the electron's forward direction, although the actual angular distribution
and collected fraction depend on the electron phase space, polarization,
collision geometry, observation aperture, and selected model.

This physical picture is broader than the familiar weak-field scaling. Linear
Thomson scattering neglects recoil and finite laser-strength effects. Exact
linear Compton kinematics retains single-photon recoil. Nonlinear ICS accounts
for electron motion in a finite-strength laser field; a modeled harmonic
location does not by itself establish that harmonic's relative intensity.

## The kinematic idea

Let \(K_e\) be electron **kinetic** energy and \(m_ec^2\) be electron rest
energy. The Lorentz factor and normalized electron speed are

\[
\gamma = 1 + \frac{K_e}{m_ec^2},
\qquad
\beta = \frac{v}{c}.
\]

The collision angle \(\alpha\) is measured between the electron and laser
propagation vectors: \(0^\circ\) is co-propagating and \(180^\circ\) is
head-on. The observation angle \(\theta\) is measured from the electron
propagation direction, so \(\theta=0\) is forward observation.

For incident laser-photon energy \(E_L\) and scattered-photon energy \(E_s\),
the exact linear coplanar relation used by pyEUVICS is

\[
E_s = E_L\,
\frac{1-\beta\cos\alpha}
{1-\beta\cos\theta +
\dfrac{E_L}{\gamma m_ec^2}\left[1-\cos(\alpha-\theta)\right]}.
\]

The final denominator term is photon recoil. In the weak-field, recoil-free,
head-on, on-axis relativistic limit,

\[
E_s\simeq4\gamma^2E_L,
\qquad
\lambda_s\simeq\frac{\lambda_L}{4\gamma^2},
\]

where \(\lambda_L\) and \(\lambda_s\) are vacuum wavelengths. These are limiting
scalings, not the general EUVICS model. See the
[science and conventions guide](../software/science.md) for the locked
pyEUVICS equations, assumptions, and validity boundaries.

## How EUV radiation is produced

1. Generate an electron bunch and accelerate it to a stated **kinetic** energy.
2. Transport, steer, diagnose, and focus the electrons.
3. Deliver, synchronize, characterize, and focus the laser pulse.
4. Overlap both beams in space and time at the interaction point with a defined
   crossing geometry.
5. Collect forward-scattered EUV photons within a defined angular acceptance.
6. Transport, spectrally analyze, and detect the EUV with calibrated optics and
   diagnostics.
7. Characterize and transport or dispose of the residual electron and laser
   beams safely.

Ideal single-particle kinematics becomes useful source output only when timing,
transverse alignment, focal overlap, collision angle, observation aperture, and
downstream acceptance are controlled and measured.

## What sets wavelength, spectrum, and signal

| Quantity | Principal controls and required conventions |
| --- | --- |
| Central wavelength or photon energy | Electron kinetic energy, laser vacuum wavelength, collision angle \(\alpha\), observation angle \(\theta\), recoil, normalized laser strength \(a_0\), polarization, and harmonic number where applicable. |
| Bandwidth and angular distribution | Electron kinetic-energy spread, emittance and divergence, laser bandwidth and intensity distribution, pointing and collision-angle jitter, nonlinear broadening, observation aperture, and correlations. Every width must state RMS, FWHM, or another explicit convention. |
| Photon yield | Electron bunch charge, laser photon number, transverse beam sizes, pulse durations, spatial and temporal overlap, crossing-angle reduction, applicable cross section, and angular or spectral acceptance. |
| Optical throughput | Geometric collection and the wavelength-dependent efficiency, incidence-angle convention, aperture, filter, grating, contamination, and alignment model of each optical stage. |
| Detector signal | Transported spectrum, detector interception and wavelength-dependent responsivity, electronics transfer and bandwidth, acquisition processing, repetition rate for average quantities, and calibration provenance. |

In the documented pyEUVICS Gaussian conventions, electron spatial widths,
energy spread, and divergence are one RMS; laser waist is the transverse
(1/e^2) intensity radius; laser duration is intensity FWHM; and laser
fractional bandwidth is one RMS. Peak intensity, pulse-average intensity, peak
power, and repetition-rate-average power are distinct. Matching a target central
wavelength does not establish sufficient photon yield, bandwidth, brilliance,
optical throughput, or detector signal.

## What pyEUVICS calculates

At the locked source version, pyEUVICS documents:

- exact linear Compton and recoil-free Thomson kinematics;
- nonlinear effective-mass and harmonic-location estimates;
- seeded approximate spectrum sampling and spectral statistics;
- Gaussian overlap, cross-section selection, photon yield, and power accounting;
- wavelength-resolved optical transport and detector/electronics response;
- configuration-driven end-to-end workflows and benchmark comparisons.

Explore the approved [installation](../software/installation.md),
[science](../software/science.md), [API](../software/api.md),
[tutorial](../software/tutorials.md), [workflow](../software/workflows.md), and
[validation](../software/validation.md) pages. The current sampled spectrum is
not a complete nonlinear radiation spectrum, and nonlinear harmonic locations
are not relative harmonic yields. Optical efficiencies and detector
responsivities require configuration-specific provenance. A nondispersive
photodiode measures integrated signal rather than wavelength directly.

## Design and validation status

| Item | Status | Meaning |
| --- | --- | --- |
| Project physics narrative | **Public draft — approved for website use** | The source wording and limitations are allowlisted; this is not approval of a completed facility design. |
| 3 MeV electron energy and 800 nm laser wavelength | **Assumed inputs — approval pending** | The electron value is explicitly kinetic energy. These are nominal study inputs, not measured operating points. |
| 6.7 nm and 13.5 nm cases | **Design targets** | Target wavelengths are not evidence of achieved output, adequate yield, or detected signal. |
| 6.7 nm CAIN comparison | **Known disagreement** | The CAIN input deck, version, aperture, beam distributions, and spectral-feature definition are incomplete; no empirical correction is justified. |
| 13.5 nm reference case | **Provisional** | No independent simulation or calibrated hardware measurement has been supplied. |
| Synthetic detector calibration | **Workflow demonstration** | It verifies software plumbing only and is not measured detector calibration. |
| EUVICS source performance | **Not measured** | No public facility measurement is claimed by the approved overview sources. |

## Sources and further reading

The project statements and equations on this page summarize the exact
public-draft sources approved by the locked EUVICS publication manifest. Model
scope and validation statements also follow the locked pyEUVICS documentation.
The assembled site records both immutable source commits, the approved source
paths, checksums, versions, statuses, and limitations in its provenance
inventory.

Primary physics references include:

- C. Sun and Y. K. Wu, “Theoretical and Simulation Studies of Characteristics
  of a Compton Light Source,”
  [Physical Review Special Topics—Accelerators and Beams (2011)](https://doi.org/10.1103/PhysRevSTAB.14.044701).
- G. A. Krafft, A. Doyuran, and J. B. Rosenzweig, “Pulsed-Laser Nonlinear
  Thomson Scattering for General Scattering Geometries,”
  [Physical Review E (2005)](https://doi.org/10.1103/PhysRevE.72.056502).
- F. V. Hartemann and S. S. Q. Wu, “Nonlinear Brightness Optimization in
  Compton Scattering,”
  [Physical Review Letters (2013)](https://doi.org/10.1103/PhysRevLett.111.044801).

The Proposal and CDR PDFs remain excluded because their separate release and
figure-permission gates are unresolved.
