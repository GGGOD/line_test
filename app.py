import requests
import re
from bs4 import BeautifulSoup
from collections import defaultdict
from flask import Flask, request, abort
import jieba
import pandas
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
# READ EXCEL
qa_df = pandas.read_excel('qa.xlsx')	

app = Flask(__name__)
#Channel access token  填入LINE 機器人的Channel access token
line_bot_api = LineBotApi('')
#Channel secret    填入LINE 機器人的Channel secret
handler = WebhookHandler('')



# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    #print("body:",body)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


def appleNews():
    res = requests.get('https://tw.appledaily.com/new/realtime')
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index,news in enumerate(soup.select('.rtddt a'), 1):
        #print(news)
        if index == 11:
            return content
        if news.select_one('h1') and index <=10:
            title    = news.select('h1')[0].text
            category = news.select('h2')[0].text
            dt       = news.select('time')[0].text
            link     = news['href']
            data     = (str(index) + '.' + dt + title + category + "\n" + link)
            #print(data)
        content  += '{}\n'.format(data)
        #print(content)
    return content


def getQA(knowledge,q, similarity):
    q_seg = ' '.join(jieba.cut(q))
    corpus    = [q_seg]
    questions = [q]
    answers   = ['NONE']
    for qa in knowledge.iterrows():
        corpus.append(' '.join(jieba.cut(qa[1]['question'])))
        questions.append(qa[1]['question'])
        answers.append(  qa[1]['answer'])
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(corpus)
    cs = cosine_similarity(X)
    rank = cs[0].argsort()[::-1]
    qa_dic = {}
    qa_dic['question'] = questions[rank[1]]
    qa_dic['answer']   = answers[rank[1]]
    qa_dic['similarity']   = cs[0][rank[1]]
    if qa_dic['similarity'] >= similarity:
        return qa_dic
    else:
        qa_dic['answer'] = '你的問題現在對我而言有點複雜, 我還要持續學習, 等我以後變聰明以後再回答你'
        return qa_dic


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # cmd = defaultdict(default_factory, command)
    reply_command = 'Hi，很高興可以為您服務' 
    #content = reply_command2
    applnews = ['news','apple','新聞']
    eiptxt0 = ['hi','hello']
    light  = '􀄃􀅷lightbulb􏿿'
    heart  = '􀄃􀄷heart􏿿'
    print(event.message.text)
    print(type(event.message.text))
    if event.message.text.lower() in eiptxt0:
        #print(reply_command)
        content = reply_command + heart
    if event.message.text in applnews:
        content = appleNews()
    else:
        question = event.message.text
        content = getQA(qa_df,question,0.1).get('answer')

    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=content))


if __name__ == '__main__':
    app.run()
