import uuid

from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Response, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse

import uvicorn

from routes.category import router as category_routes
from routes.parcel import routes as parcel_routes
from routes.page import router as page_routes


templates = Jinja2Templates(directory="templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(parcel_routes)
app.include_router(category_routes)
app.include_router(page_routes)


@app.middleware('http')
async def get_session_id(request: Request, call_next):
    session_id = request.session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['session_id'] = session_id
    responce = await call_next(request)
    return responce


app.add_middleware(SessionMiddleware, secret_key='default')

if __name__ == '__main__':
    uvicorn.run(app='main:app', host='0.0.0.0', port=8081, reload=True, log_level='debug')
