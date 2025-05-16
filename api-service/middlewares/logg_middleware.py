# Imports
# Standard Library Imports
import time
from datetime import datetime
from typing import Callable, Coroutine, Any

# Third-Party Imports
from fastapi import Request
from fastapi.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

# Local Imports
from database.postgre import get_db


############################################################################################################
# Logging Middleware Definition
############################################################################################################
class LoggMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Coroutine[Any, Any, JSONResponse]],
):
        '''Logs the request, response, time and other details of the request of each user'''
        try:
            req_body = await request.body()
            req_body_str = req_body.decode("utf-8") if req_body else "{}"
        except Exception:
            req_body_str = "{}"

        start_time = time.perf_counter()
        response =await call_next(request)
        process_time = time.perf_counter() - start_time

        body = [section async for section in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(body))

        try:
            res_body_str = body[0].decode()[:255]
        except Exception:
            res_body_str = None
        
        log_entry = {
            "path": str(request.url),
            "method": request.method,
            "request_body": req_body_str,
            "response_body": res_body_str,
            "process_time": process_time,
            "timestamp": datetime.now(),
        }

        async for db in get_db():
            await self.save_log(db, log_entry)
            break 

        return response


    async def save_log(
        self,
        db: AsyncSession,
        log_entry
    ):
        '''Saves the log entry to the database'''
        query = text("""
            INSERT INTO stac_metadata.log_entry (path, method, request_body, response_body, process_time, timestamp)
            VALUES (:path, :method, :request_body, :response_body, :process_time, :timestamp)
        """)
        try:
            await db.execute(query, log_entry)
            await db.commit()
        except Exception as e:
            print(f"Error saving log entry: {e}")
            await db.rollback()