from pyppeteer import launch
from pyppeteer.errors import TimeoutError
import json
import asyncio
import time

duoUrl = 'https://www.duolingo.com'

def getLogin():
    loginPath = 'Assets/login.txt'
    try:
        loginFile = open(loginPath, 'r')
        login = loginFile.readlines()[0]
        login = json.loads(login)
        
    except FileNotFoundError:
        loginFile = open(loginPath, 'w')
        
        login = {}
        login['user'] = input('Duolingo Username: ')
        login['pass'] = input('Duolingo Password: ')

        loginJson = json.dumps(login)
        loginFile.write(loginJson)
        
    return login['user'], login['pass']
        
async def login():
    userSelector = '#overlays > div:nth-child(5) > div > div > form > div:nth-child(1) > div._3jeu0 > div:nth-child(1) > label > div > input'
    passSelector = '#overlays > div:nth-child(5) > div > div > form > div:nth-child(1) > div._3jeu0 > div:nth-child(2) > label > div._2rjZr > input'
    duoSubmit = '#overlays > div:nth-child(5) > div > div > form > div:nth-child(1) > button'
    loginSelector = '#root > div > div > span:nth-child(2) > div > div._18cH1 > div._3wkBv > div._3uMJF > button'
    
    await asyncio.wait([
        page.click(loginSelector),
        page.waitForNavigation(),
    ])

    duoUser, duoPass = getLogin()
    
    await page.type(userSelector, duoUser)
    await page.type(passSelector, duoPass)
    
    await asyncio.wait([
        page.click(duoSubmit),
        page.waitForNavigation(),
    ])
    
async def storySelect():
    storiesInitial = '#root > div > div._1kJpR._3g2C1 > div._1bdcY > div:nth-child(3) > a > span'
    storiesBase = '//*[@id="root"]/div/div[4]/div/div/div[2]/div/div[1]/div[Set]/div[story]'
    storiesClickBase = '//*[@id="root"]/div/div[4]/div/div/div[2]/div/div[1]/div[Set]/div[story]/div[2]/div/div[1]/a[1]'
    xpBase = '//*[@id="root"]/div/div[4]/div/div/div[2]/div/div[1]/div[Set]/div[story]/div[2]/div[2]'
    noThanks = 'button[data-test="notification-drawer-no-thanks-button"]'
    with open('Assets/select.js') as script:
        executeBase = str(script.read())
    await asyncio.wait([
        page.goto(duoUrl + '/stories'),
        page.waitForNavigation(),
    ])

    for Set in range(2, 71, 1):
        for story in range(2, 6, 1):
            storyXpath = '//*[@id="root"]/div/div[4]/div/div/div[2]/div/div[1]/div[2]/div[2]/div[1]/div[1]/div/img'
            await page.waitForXPath(storyXpath)
            executeScript = executeBase.replace('set = replace', f'set = {Set}').replace('story = replace', f'story = {story}')
            click = await page.evaluate(executeScript)
            
            if click == 1:
                continue
            
            await storyComplete()
            
async def waitForEnabled(selector, timeout=30):
    await page.waitForSelector(selector)
    disabled = True
    startTime = time.time()
    while disabled:
        disabled = await page.evaluate(f'''() => {{
            finalButton = document.querySelector('{selector}');
            return finalButton.disabled
            }}''')
        if disabled:
            if time.time() - startTime > timeout:
                return 1
    return 0
            
async def match():
    for offset in range(5):
        for i in range(5):
            individualOffset = 5 + ((i + offset) % 5)
            await page.evaluate(f'''() => {{
                let tokens = document.querySelectorAll('button[data-test="challenge-tap-token"]');
                for (let i=0; i < tokens.length; i++) {{
                    if (tokens[i].classList.contains('pmjld')) {{
                        tokens[i].click()
                    }}
                }}
                if (!tokens[{i}].disabled && !tokens[{individualOffset}].disabled) {{
                    tokens[{i}].click()
                    tokens[{individualOffset}].click()
                }}
                }}''')
        time.sleep(1)
        
            
async def storyComplete():
    continueSelector = '#root > div > div > div > div > div:nth-of-type(3) > div > div > div > button'
    writeExersize = 'Buenos diás, buenos diás, buenos diás, buenos diás, buenos diás, buenos diás, buenos diás.'
    choiceSelector = 'button[data-test="stories-choice"]'
    tapTokenSelector = 'button[data-test="challenge-tap-token"]'
    finalSelector = 'button[data-test="stories-player-done"]'
    altFinal = 'button[data-test="stories-player-continue"]'
    pairCorrect = 'aria-disabled="true"'
    textSelector = 'textarea[placeholder="Type your response in Spanish!"]'
    write = True
    selectedClass = "button.classList.contains('pmjld')"
    await page.waitForSelector(continueSelector)
    
    while True:
        try:
            disabled = await page.evaluate('''
                        () => {
                           continueButton = document.querySelector('#root > div > div > div > div > div:nth-of-type(3) > div > div > div > button')
                           return continueButton.disabled
                        }
                        ''')
            if disabled != 'true':
                await page.click(continueSelector)
        except:
            break
        else:
            await page.evaluate('''() => {
            let choices = document.querySelectorAll('button[data-test="stories-choice"]');
            if (choices != undefined && choices.length != 0) {
                for (let i=0; i <= choices.length; i++) {
                    try {
                        choices[i].click();
                        }
                    catch (err) {
                        break;
                        }
                    }
                }
            }''')
            
            checkWrite = await page.evaluate('''() => {
                                            return document.querySelector('textarea[placeholder="Type your response in Spanish!"]') != null;
                                            }''') == 'true'
            
            if write and checkWrite:
                await page.type(textSelector, writeExersize)
                write = False
                
            tokensLength = await page.evaluate('''() => {
                let tokens = document.querySelectorAll('button[data-test="challenge-tap-token"]');
                if (tokens != null) {
                    return tokens.length;
                }
                else {
                return 0;
                } 
            }''')
            if tokensLength == 10:
                await match()
                matched = await waitForEnabled(continueSelector, timeout=3)
                while matched == 1:
                    await match()
                    matched = await waitForEnabled(continueSelector, timeout=3)
                await page.click(continueSelector)
                break

            elif tokensLength != 0:
                await page.evaluate('''() => {
                    let tokens = document.querySelectorAll('button[data-test="challenge-tap-token"]');
                        for (let i=0; i <= tokens.length; i++) {
                            try {
                                tokens[i].click()
                                }
                            catch (err) {
                                break;
                                }
                            }
                    }''')
    await page.evaluate('''() => {
        window.onbeforeunload = null;
    }''')
    try:
        await page.waitForSelector(finalSelector, {'timeout': 4000})
        await waitForEnabled(finalSelector)
        await asyncio.wait([
            page.goto('https://www.duolingo.com/stories'),
            page.waitForNavigation(),
        ])
    except:
        await page.waitForSelector(altFinal, {'timeout': 4000})
        await waitForEnabled(altFinal)
        await asyncio.wait([
            page.click(altFinal),
            page.waitForNavigation(),
        ])
    try:
        storyXpath = '//*[@id="root"]/div/div[4]/div/div/div[2]/div/div[1]/div[2]/div[2]/div[1]/div[1]/div/img'
        await page.waitForXPath(storyXpath, {'timeout': 5000})
    except:
        await page.waitForSelector(finalSelector, {'timeout': 4000})
        await waitForEnabled(finalSelector)
        await asyncio.wait([
            page.goto('https://www.duolingo.com/stories'),
            page.waitForNavigation(),
        ])
      
async def main():
    global browser
    global page
    headlessInput = input('Run in background? (y/n): ')
    if headlessInput.lower() == 'y':
        headless = True
    elif headlessInput.lower() == 'n':
        headless = False
    else:
        headless = None
    while headless == None:
        headlessInput = input('Invalid input. Run in background? (y/n): ')
        if headlessInput.lower() == 'y':
            headless = True
        elif headlessInput.lower() == 'n':
            headless = False
        else:
            headless = None
    browser = await launch(headless=headless, args=['--mute-audio'])
    page = await browser.newPage()
    await page.goto(duoUrl)

    await login() #Login with provided credientials
    await storySelect()
    
    await browser.close()
    
if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
