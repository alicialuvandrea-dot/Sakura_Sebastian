import os
from aiohttp import web

IMG_DIR = os.path.expanduser("~/imghost/files")
os.makedirs(IMG_DIR, exist_ok=True)

async def serve_file(request):
    filename = request.match_info["filename"]
    filepath = os.path.join(IMG_DIR, filename)
    if not os.path.exists(filepath):
        raise web.HTTPNotFound()
    return web.FileResponse(filepath)

app = web.Application()
app.router.add_get("/{filename}", serve_file)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=3002)
