from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import httplib, re, sqlite3, smtplib, ConfigParser


def remove_control_chars(s):
    return (''.join([x for x in s if ord(x) < 128]))
    
def init_db():
    global conn
    global c     
    conn = sqlite3.connect('found.db')
    c = conn.cursor()
    
def flush_db():
    c.execute("DROP TABLE products")
    conn.commit()
        
def create_db():
    c.execute("CREATE TABLE if not exists products (id INTEGER PRIMARY KEY,terms text, info text)")
    conn.commit();

def find_db(terms,entry):
    if (type(terms) is list or type(terms) is tuple):
        terms  = ','.join(terms)    
    entry = remove_control_chars(entry)
    t = (terms, entry)
    
    c.execute("SELECT * FROM products WHERE terms=? AND info=?", t) ;
    if (c.fetchone()):
        return 1
    else:
        return
    
def insert_db(terms, entry):
    if (type(terms) is list or type(terms) is tuple):
        terms  = ','.join(terms)
    
    entry = remove_control_chars(entry)
    t = (terms, entry)
    c.execute("INSERT INTO products (terms,info) VALUES(?,?)",t)
    conn.commit()
        
def noticeEMail(usr, psw, fromaddr, toaddr, product):
            
    # Initialize SMTP server
    server=smtplib.SMTP(config.get('email','uri'))
    server.starttls()
    server.login(usr,psw)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Found new Kijiji ITEM!"
    msg['From'] = fromaddr
    msg['To']  = toaddr
    
    text = "Found new item on kijiji matching search terms"+product
    html = """\
    <html>
      <head></head>
      <body>
        <p>Found item on kijiji matching search terms</p>
        <p>"""
    html = html+product
    html += """\
        </p>
      </body>
    </html>
    """
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()    
    
def exists_db(terms):
    if (type(terms) is list or type(terms) is tuple):
        terms  = ','.join(terms)    
    t = (terms,)
    c.execute("SELECT * FROM products WHERE terms=?", t)
    if (c.fetchone()):
        return 1
    else:
        return
    
def is_want(product):
    return (re.search(r'Wanted', product))    
            
def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def get_result(soup, num):
    match = "resultRow"+str(num)
    
    if (soup.find(id=match)):       
        mylist = soup.find(id=match).findAll("td")
        mylink =  soup.find(id=match).a
        desc = mylist[2]
        desc = remove_html_tags(str(desc))    
        return (str(mylink) + desc)
    else:
        return
    
def process_first_page(search):
    pagenum = 1;
    
    if pagenum == 1:
        pagestr = "isSearchFormZtrue"
    else:
        pagestr = "PageZ"+pagenum

    httpconn = httplib.HTTPConnection(config.get('app', 'city'))
    if (type(search) is list or type(search) is tuple):
        searchstr1 = "-".join(search)
        searchstr2 = "Q20".join(search)
    else:
        searchstr1 = search
        searchstr2 = search
        


    querystr = "/f-"+searchstr1+"-Classifieds-W0QQKeywordZ"+searchstr2+"QQ"+pagestr
    httpconn.request("GET", querystr)
    
    r1 = httpconn.getresponse()
    print r1.status, r1.reason
    data1 = r1.read()
    soup = BeautifulSoup(data1)
    some = 0    
    exists = exists_db(search)  
    
    for i in reversed(range(config.getint('app', 'items'))):        
        product = get_result(soup, i)        
        if (product and not is_want(product)):
            some = 1
            
            found = find_db(search,product);
            if (not found):
                print "Product not found in DB..."+str(i)
                if (exists):
                    print "Sending email notification about product "+str(i)
                    noticeEMail(config.get('email','user'), config.get('email', 'pass'), config.get('email', 'from'), config.get('email', 'to'), product)
                print "inserting product into db..."
                insert_db(search,product)
            else:
                print "Found product already in DB..."+str(i)
                
    if (not some and not exists):
        insert_db(search,'FILLER')
                
'''
main
'''
if __name__ == '__main__':
    global config
    
    config = ConfigParser.RawConfigParser()
    config.read('settings.cfg')
    
    init_db()
    if (config.getboolean('app', 'flush')):
        flush_db()
        
    create_db()
    
       
    search_list = config.items( "searches" )
    
    for key,search in search_list:
        terms = search.split(',')
        print "searching for:  "+str(terms)
        process_first_page(terms)
    
    
    
    
    
    
    







