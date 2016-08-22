#!/usr/bin/env python

import config
import json
import logging
import os
import telebot
import sqlite3

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(name)10s] [%(levelname)s] %(message)s')
logging.getLogger("requests").setLevel(logging.ERROR)
logger = logging.getLogger('cli')
logger.setLevel(logging.INFO)

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  logger.info('"'+message.text+'" from ['+str(message.from_user.id)+'] '+message.from_user.first_name+" "+message.from_user.last_name+" ("+message.from_user.username+")")
  result=(
    "Commands: ",
    "/info [bot name] - info about bot"
  )
  bot.send_message(message.from_user.id, "\n".join(result))

def send_info(name,message):
  inv=[]
  try:
    with open(os.path.join(config.bot_path+"/web","inventory-"+name+".json")) as f:
      inv=json.load(f)
    stats=parse_stats(inv)
    conn=sqlite3.connect(os.path.join(config.bot_path+"/data",name+".db"))
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT COUNT(encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")
    catch_day=cur.fetchone()[0]
    cur.execute("SELECT DISTINCT COUNT(pokestop) FROM pokestop_log WHERE dated >= datetime('now','-1 day')")
    ps_day=cur.fetchone()[0]
    conn.close()
    result=(
      "*"+name+"*:",
      "_Level:_ "+str(stats["level"]),
      "_XP:_ "+str(stats["experience"]-stats["prev_level_xp"])+"/"+str(stats["next_level_xp"]-stats["prev_level_xp"]),
      "_Pokemons Captured:_ "+str(stats["pokemons_captured"])+" ("+str(catch_day)+") _today_",
      "_Poke Stop Visits:_ "+str(stats["poke_stop_visits"])+" ("+str(ps_day)+" _today_)",
      "_KM Walked:_ "+str(stats["km_walked"])
    )
    bot.send_message(message.from_user.id, "\n".join(result),parse_mode="Markdown")
    with open(os.path.join(config.bot_path+"/web","location-"+name+".json")) as f:
      loc=json.load(f)
    bot.send_location(message.from_user.id,loc["lat"],loc["lng"])

  except IOError as e:
    logging.error("I/O error: "+str(e))

@bot.message_handler(commands=['info'])
def get_info(message):
  logger.info('"'+message.text+'" from ['+str(message.from_user.id)+'] '+message.from_user.first_name+" "+message.from_user.last_name+" ("+message.from_user.username+")")
  sp=message.text.split(' ')
  if len(sp)>1:
    if sp[1] in config.bots:
      send_info(sp[1], message)
    else:
      bot.send_message(message.from_user.id,"Unknown bot "+sp[1])
  else: 
    for name in config.bots:
      send_info(name,message)

def parse_stats(inv):
  for item in inv:
    if "player_stats" in item["inventory_item_data"]:
      return item["inventory_item_data"]["player_stats"]
  return None
def main():
  logger.info("Bot started. Enjoy!")
  bot.polling()


if __name__ == '__main__':
  main()
