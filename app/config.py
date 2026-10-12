from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_language:str='pl';apify_api_token:str='';azure_translator_key:str='';azure_translator_region:str='';azure_translator_endpoint:str='https://api.cognitive.microsofttranslator.com'
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
