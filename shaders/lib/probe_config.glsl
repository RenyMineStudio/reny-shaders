#ifndef RENY_PROBE_CONFIG_GLSL
#define RENY_PROBE_CONFIG_GLSL

/*
 * Reny Shaders — Architecture Capability Probe
 * Target Stack: Minecraft 1.7.10 / Forge 10.13.4.1614 / OptiFine HD U E7
 *
 * Probe Modes:
 * 0 = Baseline Pass-Through (verifies core stack rendering and vanilla fidelity)
 * 1 = Capability & Uniform Probe (tests frameCounter, frameTime, sunPosition, includes)
 * 2 = History & Skip-Clear Probe (tests colortex persistence across motion and state switches)
 * 3 = Material ID Mapping Probe (tests block.properties and Forge namespaced aliases)
 * 4 = Buffer Formats Probe (tests RGBA16F, R11F_G11F_B10F, RGBA32F attachments)
 * 5 = Deferred Pass Probe (tests deferred execution stage between terrain and water)
 */

#define PROBE_MODE 0 // [0 1 2 3 4 5]

#define PROBE_MODE_BASELINE   0
#define PROBE_MODE_CAPABILITY 1
#define PROBE_MODE_HISTORY    2
#define PROBE_MODE_MATERIAL   3
#define PROBE_MODE_FORMATS    4
#define PROBE_MODE_DEFERRED   5

/*
 * Magic signature values used to verify inter-pass communication
 */
#define RENY_DEFERRED_MAGIC vec4(0.24, 0.48, 0.72, 1.0)
#define RENY_PROBE_VERSION  10710

#endif // RENY_PROBE_CONFIG_GLSL
