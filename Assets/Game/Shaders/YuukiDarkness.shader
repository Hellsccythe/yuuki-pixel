// Full-screen darkness for the 2D top-down maps (built-in render pipeline).
// A quad in front of the camera darkens the scene by the ambient amount and cuts warm
// pools of light around up to 32 points (torches, street lamps, windows, the stove).
// The light is quantized into a few steps so it matches the pixel-art look.
Shader "Yuuki/Darkness"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" "PreviewType"="Plane" }
        Cull Off
        ZWrite Off
        ZTest Always
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #include "UnityCG.cginc"

            #define MAX_LIGHTS 32

            float4 _Lights[MAX_LIGHTS];       // xy world position, z radius, w intensity
            float4 _LightColors[MAX_LIGHTS];  // rgb glow colour
            float _LightCount;
            float4 _Ambient;                  // rgb shadow tint, a darkness 0..1
            float _Steps;                     // 0 = smooth
            float _GlowStrength;

            struct appdata { float4 vertex : POSITION; };
            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 world : TEXCOORD0;
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.world = mul(unity_ObjectToWorld, v.vertex).xy;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float light = 0;
                float3 glow = 0;
                int count = (int)_LightCount;
                for (int k = 0; k < MAX_LIGHTS; k++)
                {
                    if (k >= count) break;
                    float2 d = i.world - _Lights[k].xy;
                    d.y *= 1.3; // the ground is seen at an angle: pools are wider than tall
                    float f = saturate(1.0 - length(d) / max(_Lights[k].z, 0.001));
                    f = f * f * (3.0 - 2.0 * f) * _Lights[k].w;
                    light += f;
                    glow += _LightColors[k].rgb * f;
                }
                float lit = saturate(light);
                if (_Steps > 0) lit = floor(lit * _Steps + 0.35) / _Steps;
                glow = glow / max(light, 0.0001);

                float dark = _Ambient.a * (1.0 - lit);
                float glowAlpha = lit * _GlowStrength * saturate(_Ambient.a * 1.6);
                float alpha = saturate(dark + glowAlpha);
                float3 rgb = (dark * _Ambient.rgb + glowAlpha * glow) / max(dark + glowAlpha, 0.0001);
                return fixed4(rgb, alpha);
            }
            ENDCG
        }
    }
    Fallback Off
}
