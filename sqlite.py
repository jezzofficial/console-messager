import sqlite3 as sq

async def db_start():
    try:
        global db, cur
        db = sq.connect('LOGS.db')
        cur = db.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS profile (
                username TEXT,
                adm TEXT,
                STATUS TEXT,
                MESSAGERS INTEGER,
                ban TEXT
            )
        ''')
        db.commit()
    except:
        return False
async def create(username):
    user = cur.execute("SELECT 1 FROM profile WHERE username == '{key}'".format(key=username)).fetchone()
    if not user:
        cur.execute("INSERT INTO profile VALUES(?,?,?,?,?)", (username,"False","Online",0, "False"))
        db.commit()

async def getstatus(username):
    getst = cur.execute("SELECT STATUS FROM profile WHERE username = ?", (username,)).fetchone()
    if getst:
        return getst[0]
    else:
        return None

async def updatestatus(username, status):
    cur.execute("UPDATE profile SET STATUS = ? WHERE username == ?", (status, username))
    db.commit()

async def updateadm(username, why):
    cur.execute("UPDATE profile SET adm = ? WHERE username == ?", (why, username))
    db.commit()

async def checkadm(username):
    getst = cur.execute("SELECT adm FROM profile WHERE username = ?", (username,)).fetchone()
    if getst[0] == "True":
        return True
    else:
        return False

async def checkban(username):
    getban = cur.execute("SELECT ban FROM profile WHERE username = ?", (username,)).fetchone()
    if getban[0] == "True":
        return True
    else:
        return False

async def getmes(username):
    getmess = cur.execute("SELECT MESSAGERS FROM profile WHERE username = ?", (username,)).fetchone()
    if getmess:
        return getmess[0]
    else:
        return None

async def updatemes(username):
    cur.execute("UPDATE profile SET MESSAGERS = ? WHERE username == ?", (await getmes(username) + 1, username))
    db.commit()

async def getban(username):
    cur.execute("UPDATE profile SET ban = ? WHERE username == ?", ("True", username))
    db.commit()

async def rmban(username):
    cur.execute("UPDATE profile SET ban = ? WHERE username == ?", ("False", username))
    db.commit()


