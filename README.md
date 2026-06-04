# TUS Uploader

A secure resumable uploader built with FastAPI, `tus`, `python-dotenv`, and a responsive Uppy-based frontend.

![img.png](static/ScreenShot.png)

## Features

- Chunked upload flow with `POST`, `HEAD`, `PATCH`, and `OPTIONS` endpoints based on the tus 1.0 protocol
- No database; upload state is stored in `tmp/<UPLOAD_ID>.tus`
- Final files are stored in `uploads/` with `uuid`-based names
- The original filename is not used for storage
- Direct static file links served from `BASE_URL/uploads/...`
- Frontend with drag-and-drop upload, inline direct link display, progress, speed, ETA, retry/resume, and light/dark themes
- Optional upload password from `.env`

## Project Structure

```text
.
├── main.py
├── utils/
│   ├── config.py
│   ├── middlewares.py
│   ├── routes.py
│   ├── storage.py
│   └── validators.py
├── requirements.txt
├── .env.sample
├── static/
│   ├── app.css
│   ├── app.js
│   ├── favicon.ico
│   ├── index.html
│   └── logo.png
├── tmp/
└── uploads/
```

## Environment

Copy `.env.sample` into `.env` if needed. The repo already contains a local `.env` for development.

### Env Description

| Variable | Default | Example | Description |
| --- | --- | --- | --- |
| `DEBUG` | `NO` | `YES` | Enables FastAPI debug mode and uvicorn reload when set to `YES`. |
| `PORT` | `8989` | `8989` | Port used when running `python main.py`. |
| `BASE_URL` | `http://localhost:<PORT>` | `https://upload.example.com` | Public base URL used for TUS `Location` headers and final download links. |
| `CORS_ALLOWEDS` | `BASE_URL`, localhost variants | `https://app.example.com,https://upload.example.com` | Comma-separated allowed browser origins for upload requests. Include the exact origin where the frontend is opened. |
| `MAX_UPLOAD_SIZE` | `1073741824` | `2147483648` | Maximum allowed file size in bytes. |
| `CHUNK_SIZE` | `1048576` | `5242880` | TUS chunk size in bytes used by the frontend uploader. |
| `UPLOAD_PASSWORD` | `1234` | `change-me` | Optional upload password. Set it to an empty value to disable password protection. |
| `UPLOAD_DIRECTORIES` | empty | `documents,images,clients/acme` | Optional comma-separated destination folders inside `uploads/`. When set, the frontend shows a destination select field. Absolute paths and `..` are rejected. |
| `LOGO_URL` | `/static/logo.png` | `/static/my-logo.svg` | Logo URL used in the page header. It can be a `/static/` path or a full external URL. |
| `FAVICON_URL` | `/static/favicon.ico` | `/static/my-favicon.png` | Browser favicon URL. It can be a `/static/` path or a full external URL. |

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Because `main.py` loads `.env` and starts `uvicorn` with the configured port, run:

```bash
python main.py
```

Then open:

```text
http://localhost:8989
```

## Tests

Run the test suite with the standard library unittest runner:

```bash
python -m unittest discover -s tests
```

## Docker

Build and run the container on port 80:

```bash
docker build -t tus-uploader .
docker run -p 80:80 tus-uploader
```

For production deployments, `uploads` and `tmp` can be defined as Docker-managed volumes or mounted from a host disk path so uploaded files and resumable upload state survive container replacement. The Dockerfile does not define these mounts directly; configure them in your Docker run command, Compose file, or deployment platform.

## API

### Create upload

`POST /files`

Required headers:

- `Tus-Resumable: 1.0.0`
- `Upload-Length: <bytes>`
- `Upload-Metadata: filename <base64>,filetype <base64>`
- `X-Upload-Password: <password>` when `UPLOAD_PASSWORD` is set

### Check offset

`HEAD /files/{upload_id}`

### Send chunk

`PATCH /files/{upload_id}`

Required headers:

- `Tus-Resumable: 1.0.0`
- `Content-Type: application/offset+octet-stream`
- `Upload-Offset: <current_offset>`
- `X-Upload-Password: <password>` when `UPLOAD_PASSWORD` is set

### Get direct link

`GET /api/files/{upload_id}/link`

### Download file

`GET /uploads/{uuid-and-extension}`

## Security Notes

- Files are only accepted from an explicit extension and MIME allowlist
- Stored filenames are randomized UUIDs
- Upload creation and chunk transfer can be protected with `UPLOAD_PASSWORD`
- Final files are exposed directly from `/uploads/`
- `X-Content-Type-Options: nosniff` and other baseline headers are applied
- `.tus` state files are removed automatically after a successful upload
