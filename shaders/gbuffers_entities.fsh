#version 120

/*
 * Reny Shaders — Entities GBuffer Fragment Shader
 */

/* DRAWBUFFERS:012 */

uniform sampler2D texture;
uniform sampler2D lightmap;
uniform vec4 entityColor;
uniform int entityId;

varying vec4 color;
varying vec2 texcoord;
varying vec2 lmcoord;
varying vec3 normal;

void main() {
    vec4 texColor = texture2D(texture, texcoord);
    if (texColor.a < 0.1) discard;

    vec4 light = texture2D(lightmap, lmcoord);
    vec4 baseColor = texColor * color * light;

    // Apply hurt flash / entity overlay color if present
    baseColor.rgb = mix(baseColor.rgb, entityColor.rgb, entityColor.a);

    gl_FragData[0] = baseColor;
    gl_FragData[1] = vec4(normal * 0.5 + 0.5, 1.0);
    gl_FragData[2] = vec4(float(entityId) / 255.0, 0.5, 1.0, 1.0);
}
