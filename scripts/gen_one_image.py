import json, io, sys, time
from PIL import Image
from google import genai
from google.genai import types
prompt, out = sys.argv[1], sys.argv[2]
config = json.load(open('/home/shinyyume/.openclaw/openclaw.json'))
api_key = config['models']['providers']['google']['apiKey']
client = genai.Client(api_key=api_key)
last = None
for i in range(8):
    try:
        resp = client.models.generate_content(
            model='gemini-3.1-flash-image-preview',
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=['IMAGE','TEXT'])
        )
        for part in resp.candidates[0].content.parts:
            if getattr(part, 'inline_data', None):
                Image.open(io.BytesIO(part.inline_data.data)).convert('RGB').save(out, quality=90)
                print('saved', out)
                raise SystemExit(0)
        last = RuntimeError('no image in response')
    except Exception as e:
        last = e
        print('attempt', i+1, 'failed:', repr(e), flush=True)
        time.sleep(min(60, 5*(i+1)))
raise last
