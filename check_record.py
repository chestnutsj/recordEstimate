#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import argparse
import os
import requests
# import colorama
import datetime
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from chinese_calendar import  is_workday

class Zbox:
    API_URL = ""
    def __init__(self,url):
        USER = os.getenv('ZBOX_USER')
        PASSWD = os.getenv('ZBOX_PASSWD')
        if USER is None or PASSWD is None:
            Log.error("Please set ZBOX_USER and ZBOX_PASSWD environment variables")
            exit(1)
        self.API_URL = url
        data = {}
        data['account'] = USER
        data['password']= PASSWD
        response = requests.post(self.API_URL+ "/tokens", json=data)
        if response.status_code != 201:
            Log.error(response.content.decode("unicode-escape"))
            exit(1)
        self.token = response.json()
        print(self.token)

    def get_task(self):
      response = requests.get(self.API_URL+ "/tasks?limit=100", headers=self.token)
      try:
        task = response.json()
        return task
      except Exception as e:
        print(e)
        return None
    
    def  Estimate(self, taskid):
        response = requests.get( "http://zbox.greatdb.com/zentao/task-recordEstimate-"+str(taskid) +".html", headers=self.token)
        try:
            task = response.text
            return task
        except Exception as e:
            print("ERROR:"+e)
            return None    

def  getForm(html_data):

    soup =BeautifulSoup(html_data, 'html.parser')
    form = soup.find('form', id='recordForm')
    if form is None:
        return
    table_rows = form.find_all('tr')
    if table_rows is None:
        return
    rows = []
    for tr in table_rows:
 
        td = tr.find_all('td')
        if td is None or td == []:
            continue
        #print(td)
        input_ = td[0].find_all('input')
        #print(input_)
        if input_ is None or input_ == []:
            x=[]
            for i in td[:4]:
                x.append(i.text)        
            if len(x) == 4:
                rows.append(x)
    return rows


def sort_by_t(rows):
    formatted_data = []
    for item in rows:
        date_str = item[2]
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_of_week = date.strftime("%A")
        hours = float(item[3][:-2])
        x= [ item[0], item[1],hours,day_of_week,date]
        formatted_data.append(x)

    sorted_data = sorted(formatted_data, key=lambda x:  x[-1])
    return sorted_data

# 颜色转义码
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'
 

def check_worker(tasks):
   
    start = tasks[0][-1]
    last =  datetime.now().date()
    date_work_hours={}
    date_tasks = {}
    for task in tasks:
        task_date = task[-1]
        if task_date in date_work_hours:
            date_work_hours[task_date] += task[2]
            date_tasks[task_date].append(task)
        else :
            date_work_hours[task_date] = task[2]
            date_tasks[task_date] = [task]
    d = start
    count = 0
    while d <= last:
    
        if is_workday(d):
            if d  not in date_work_hours:
                print( f"{d} : {RED}Task not working 8 hours.{RESET}")
            else:
                if  date_work_hours[d] <8 or date_work_hours[d] > 13  :
                    if date_work_hours[d] < 8:
                        print(  f"{d} : {RED}Task less < requirement of 8 hours.{RESET}")
                        for t in  date_tasks[d]:
                            print("     "+str(t))
                    else:
                        print( f"{d} : {RED}Task less > requirement of 8 hours.{RESET}")
                        for t in  date_tasks[d]:
                            print("     "+str(t))
                else :
                    print( f"{d} : {GREEN}Task requirement of  {date_work_hours[d]} hours.{RESET}")

        d += timedelta(days=1)

const_last_day=90

def is_within_last_three_months(date_str):
    assigned_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
    current_date = datetime.now()
    three_months_ago = current_date - timedelta(days=const_last_day)
    return assigned_date >= three_months_ago

if __name__ == "__main__":
    #os.environ.setdefault("ZBOX_USER", "")
    #os.environ.setdefault("ZBOX_PASSWD", "")
    #os.environ.setdefault("HTTP_PROXY", "http://192.168.5.242:7890")
    API_URL = 'http://xxxxxx/zentao/api.php/v1'
    zz = Zbox(API_URL)
    data = zz.get_task()
    const_last_day = 90
    
    undone_tasks = [task for task in data['tasks'] if is_within_last_three_months( task['assignedDate']) ]
    tasks_data=[]
    for i in undone_tasks:
        name = ""
        if 'parentName' in i :
           name =i['parentName'] +i['name'] 
        else:
           name = i['name']
        task_id = i['id']
   
        rows= getForm(zz.Estimate(task_id))
        if rows is None or rows == []:
            continue
        data = [ [task_id  , name,   row[1],  row[2] ] for i, row in enumerate(rows)]
        tasks_data.extend(data)

    tasks = sort_by_t(tasks_data)
    check_worker(tasks)    
