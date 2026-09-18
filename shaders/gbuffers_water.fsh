#version 120

/*
 * Reny Shaders — Translucent / Water GBuffer Fragment Shader
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
    if (texColor.a < 0.02) discard;

    vec4 light = texture2D(lightmap, lmcoord);
    vec4 baseColor = texColor * color * light;

    gl_FragData[0] = baseColor;
    gl_FragData[1] = vec4(normal * 0.5 + 0.5, 1.0);
    gl_FragData[2] = vec4(materialId / 255.0, fract(materialId), 1.0, 1.0);
}
