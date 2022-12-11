import os
from dotenv import load_dotenv
from pysnmp.hlapi import *
from tools.logger import Logger
from lib.libsnmp import SNMPHelper

class Poller:
  def __init__(self):
    self.logger = Logger()
    self.snmp = SNMPHelper()
    
    # load .env file
    load_dotenv()
        
    self.POLLER_ID = os.getenv('POLLER_ID')
    self.BEARER_TOKEN = os.getenv('BEARER_TOKEN')
    
    if not self.POLLER_ID:
      self.logger.log_error('POLLER_ID not defined. Update it in the .env file')
      raise Exception('POLLER_ID not defined. Update it in the .env file')
    
    if not self.BEARER_TOKEN:
      self.logger.log_error('BEARER_TOKEN not defined. Update it in the .env file')
      raise Exception('BEARER_TOKEN not defined. Update it in the .env file')
  
if __name__ == '__main__':
  poller = Poller()
  