import sys
import io
import openai
import requests
import json
import base64

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

#############################################
######## enter your api keys here ###########

openai.api_key="ENTER YOUR API KEY"# openai api key
head = {
        "Authorization": "Bearer yourapikeyhere"# github api key
    }
##############################################
##############################################

models = openai.Model.list()
for model in models["data"]:
    print(model["id"])



def getContents(url):
    urlcontent = requests.get(url,headers=head)
    urlcontent = json.loads(urlcontent.content)
    fileName = urlcontent["name"]
    fileContent = base64.b64decode(urlcontent["content"]).decode("utf-8")
    return(fileName,fileContent)

def checkname(name):
    if name[0] == ".":
        return False
    if "ignore" in name:
        return False
    else:
        return True

def filelist(fileinfo):
    l = []
    for item in fileinfo:
        if checkname(item["name"]):
            if item["type"] == "file":
                l.append((item["name"],item["download_url"]))
            else:
                ll = []
                selfcontent = requests.get(item["url"], headers=head)
                selfcontent = json.loads(selfcontent.content)
                for i in selfcontent:
                    if i["type"] == "file":
                        ll.append((i["name"],i["download_url"]))
                ll = dict(ll)
                l.append((item["name"],ll))
    return l


def git(repo):
    baseurl = "https://api.github.com/repos"
    repourl = f"{baseurl}{repo}"
    contenturl = f"{baseurl}{repo}/contents"

    mainResponse = requests.get(repourl, headers=head)
    mainContent = json.loads(mainResponse.content)

    fileResponse = requests.get(contenturl, headers=head)
    fileInfo = json.loads(fileResponse.content)

    name = mainContent["name"]
    stars = mainContent["stargazers_count"]

    fileList = filelist(fileInfo)

    return(name,stars,fileList)

def gptlist(flist):
    l = ""
    for item in flist:
        if type(item[1]) == dict:
            l+= item[0]+"/\n"
            for i in item[1]:
                l+= "\t"+i+"\n"
        else:
            l+= item[0]+"\n"
    return l
        


def gpt(fileList):
    #################### different info that me might want about the repo ####################
    fileprompt = f"{fileList} this is my file structure. i need you to tell me what you think the most important files are to analyze what my project does try to keep it around 2 files and look for files called main. try and stay away from files that could be large. please respond with the file path and nothing else" 

    chat_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": fileprompt}
        ],
        max_tokens=150,  # Adjust token length as per your file size and expected output
        temperature=0.1,  # Controls creativity in the response
    )
    analysis = chat_completion.choices[0].message['content'].strip()
    return analysis

def gptfin(info):

    prompt = f"print 1 line that tells you if crypto is mentioned within the files, then print 3 seprate lines that each start with a score of 1-10 on how closely the following files match the statement and do not repeat the statements and make sure to start with your score 1-10. line1 - the readme file is comprehensive and gives a good overview of the project, line2 - the files with code contain comments that are useful, line3 - this project is useful. this is a python dictionary with the files needed to analyze and the file contents{info}"

    chat_completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=250,  # Adjust token length as per your file size and expected output
        temperature=0.1,  # Controls creativity in the response
    )
    analysis = chat_completion.choices[0].message['content'].strip()
    return analysis

def readmeCheck(flist):
    for item in flist:
        if type(item[1]) == dict:
            for i in item[1]:
                if "README" in i or "readme" in i:
                    #print("readme found")
                    return item[1][i]
        else:
            if "readme" in item[0]:
                #print("readme found")
                return item[1]


def getinfo(flist,filesNeeded):
    fn = filesNeeded.split("\n")
    fl = dict(flist)
    rl = {}
    for f in fn:
        #f = f[0:]
        if "/" in f:
            x = f.split("/")
            link = fl[x[0]][x[1]]
            selfcontent = requests.get(link, headers=head)
            rl[f] = selfcontent.text
            
        try:
            if f in fl:
                selfcontent = requests.get(fl[f], headers=head)
                rl[f] = selfcontent.text
        except:
            pass
    rm = readmeCheck(flist)
    rm = requests.get(rm, headers=head)
    rl["README"] = rm.text

    return(rl)
                


repo = input("enter the repo you want to analyze using the format /owner/repo: ")

name,stars,flist = git(repo)
glist = gptlist(flist)
filesNeeded = gpt(glist)
info = getinfo(flist,filesNeeded)
final = gptfin(info)
print(final)
