#version 120

/*
 * Reny Shaders — Terrain GBuffer Fragment Shader
 * Tests MRT outputs (colortex0, colortex1, colortex2) and block mapping
 */

/* DRAWBUFFERS:012 */

uniform sampler2D texture;
uniform sampler2D lightmap;

varying vec4 color;
varying vec2 texcoord;
varying vec2 lmcoord;
varying vec3 normal;
varying float materialId;

void main() {
    vec4 texColor = texture2D(texture, texcoord);
    if (texColor.a < 0.1) discard;

    vec4 light = texture2D(lightmap, lmcoord);
    vec4 baseColor = texColor * color * light;

    // Buffer 0: Base illuminated color (RGBA8)
    gl_FragData[0] = baseColor;

    // Buffer 1: Surface normal in eye space [0, 1]
    gl_FragData[1] = vec4(normal * 0.5 + 0.5, 1.0);

    // Buffer 2: Material ID encoding (stored into RGBA16F attachment)
    // R = normalized ID, G = raw ID fractional part, B = 1.0 if ID is mapped (>0), A = 1.0
    float hasId = (materialId > 0.0) ? 1.0 : 0.0;
    gl_FragData[2] = vec4(materialId / 255.0, fract(materialId), hasId, 1.0);
}
