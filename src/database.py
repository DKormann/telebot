
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()


url=os.getenv('SUPABASE_URL')
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_all_chats():
    return supabase.table("chats").select("*").execute().data



def insert_chat(chat_id:int, username:str):
    supabase.table("chats").insert({"id":chat_id,"username":username}).execute()
    print(f"inserted {username}")

def get_chat_by_username(username:str):
    response = supabase.from_("chats").select("*").eq("username",username).execute()
    return response.data

def get_chat_by_id(chat_id:int):
    return supabase.from_("chats").select("*").eq("id", chat_id).execute()


print (get_chat_by_username("reaper"))


