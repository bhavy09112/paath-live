"""Serve teacher and Lecture Studio through one local gateway."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.main import app
from fastapi import Request
from fastapi.responses import Response, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn

@app.get('/studio')
def studio_redirect():
    return RedirectResponse('/studio/')

@app.api_route('/studio/{path:path}', methods=['GET', 'POST'])
async def studio_proxy(path: str, request: Request):
    # Fixed upstream; never use a user-supplied host or forward credentials.
    if request.method == 'POST':
        origin = request.headers.get('origin')
        if origin and origin.split('://', 1)[-1] != request.headers.get('host'):
            return Response('Invalid origin', status_code=403)
    client = httpx.AsyncClient(timeout=httpx.Timeout(120, connect=5))
    headers = {k: v for k, v in request.headers.items() if k.lower() in {'content-type', 'content-length'}}
    url = 'http://127.0.0.1:8765/' + path
    if request.url.query:
        url += '?' + request.url.query
    try:
        upstream = await client.send(client.build_request(request.method, url, headers=headers,
            content=request.stream() if request.method == 'POST' else None), stream=True)
    except httpx.HTTPError:
        await client.aclose()
        return Response('Lecture Studio is unavailable. Please try again later.', status_code=503)
    content_type = upstream.headers.get('content-type', 'application/octet-stream')
    if 'text/html' in content_type:
        body = (await upstream.aread()).decode('utf-8')
        await upstream.aclose()
        await client.aclose()
        body = body.replace('/api/', '/studio/api/').replace('/jobs/', '/studio/jobs/')
        body = body.replace('http://127.0.0.1:8766/', '/').replace('http://127.0.0.1:5173/', '/')
        body = body.replace('Paath Live →', 'Interactive teacher →')
        return Response(body, status_code=upstream.status_code, media_type='text/html')
    async def chunks():
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()
    return StreamingResponse(chunks(), status_code=upstream.status_code, media_type=content_type)

if __name__ == '__main__':
    app.mount('/', StaticFiles(directory=ROOT / 'frontend' / 'dist', html=True), name='frontend')
    uvicorn.run(app, host='127.0.0.1', port=8080)
