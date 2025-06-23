from fastapi import FastAPI

app = FastAPI() 


@app.get("/api/news/processed") 
async def read_root(): 
    return {"message": "Hello world"} 



@app.post("/api/news/refresh") 
async def refresh_news(): 
    ## Trigger RSS feed fetch ## 
    return {"status": "refreshed"} 




     




