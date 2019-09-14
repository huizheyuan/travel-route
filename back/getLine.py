# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 19:01:29 2019

@author: PC-shujie
"""

import pymysql
import math
import time
import copy
import numpy as np
import redis
import sys

class getLine:
    def __init__(self):
#        t = time.time()
        self.conn = pymysql.connect('119.29.229.221', 'mysql', 'MyNewPass4!', 'HC', charset='utf8')
        self.cursor = self.conn.cursor()
        
        pool = redis.ConnectionPool( host='www.indream96.com', port=6379, decode_responses=True )
        self.rd = redis.Redis( connection_pool=pool )
        
#        print( '连接数据库时间:', time.time()-t,'秒' )
        
        # =======================后端需要传入的数据=======================
        
#        self.departDate = '2019-06-13'  # 起程日期
#        departTime = '8:00:00'  # 起程时间
#        isPlane = 1  # 是否坐飞机
#        self.startPoint = '湖南工学院'  # 起点
#        self.endPoint = '天安门'  # 终点
#        self.s2eFlag = '159-131'  # 起点到终点标记
#        self.s2aFlag = 'hunan-beijing'  # 起点到机场标记
#        self.sa2eaFlag = 'hunan-beijing'  # 机场到机场标记
#        # 1：时间最短；    2：花费最少； 3:舒适度最高
#        self.requirement = '1,2'

        
        self.departDate = sys.argv[1]  # 起程日期
        departTime = sys.argv[2]  # 起程时间
        isPlane = int(sys.argv[3])  # 是否坐飞机
        self.startPoint = sys.argv[4]  # 起点
        self.endPoint = sys.argv[5]  # 终点
        self.s2eFlag = sys.argv[6]  # 起点到终点标记
        self.s2aFlag = sys.argv[7]  # 起点到机场标记
        self.sa2eaFlag = sys.argv[8]  # 机场到机场标记
        # 1：时间最短；    2：花费最少； 3:舒适度最高
        self.requirement = sys.argv[9][:-1]
#        self.requirement = 2
        
        # =============================================================
        
        self.localTraffic = {}  # 记录本地交通
        self.noLocalTraffic = []  # 记录没有本地交通的线路
        self.id4database = [0]  # 记录数据id
        
        self.startTime = time.strptime( self.departDate+' '+departTime, '%Y-%m-%d %H:%M:%S' )
        self.lineIndex = 1  # 用作标记 line1  line2
        
        # 起点到终点火车线路
        s2eTraffic = {}
        # 起点到机场火车线路
        s2aTraffic = {}
        # 机场到终点火车线路
        a2eTraffic = {}
        
        self.startAirports = []   # ['怀化芷江机场', '长沙黄花国际机场', '常德桃花源机场', '张家界荷花机场']
        
        try:
#            t = time.time()
            # 起点到终点
            s2eTraffic = self.gets2eLine()
            if isPlane==1:
                # 起点到机场
                s2aTraffic = self.gets2aLine()
                # 机场到终点
                a2eTraffic = self.geta2eLine()
#            print( a2eTraffic )
#            print('数据库查询及处理数据总时间:', time.time()-t,'秒')
        except Exception as e:
            print( e )
        finally:
            self.conn.close()
#            return
        
        traffic = dict( dict(s2eTraffic, **s2aTraffic), **a2eTraffic )
#        print(traffic)
#        return
        
        ways = list( traffic.keys() )
        
        lines = []  # [['line1', 'line2', 'line3'], ['line4', 'line5'], ['line6', 'line7'], ['line8'], ['line9', 'line10']]
        for way in ways:
            lines.append( list(traffic[way].keys()) )
        self.lines = [ l   for i in lines  for l in i ]
#        print(len(lines))
#        print(lines)
#        t = time.time()
        weights = self.getWeight( traffic, self.startPoint, self.endPoint, self.startTime ,self.startAirports,self.lines )
#        print( '矩阵时间:',time.time()-t,'秒' )
#        print(weights)
#        t = time.time()
#        path, pathDistance = self.dijkstra( weights, 0 )
#        print( '算法时间:',time.time()-t,'秒' )
#        print( path[-1] )
#        print( pathDistance[-1] )
        
        # =======================返回给后端的id=======================
#        returnId = []
#        for index in path[-1].split('>')[1:-1]:
#            # index表示第几条线，在lines里面找到对应的线路编号(line75)
#            lineNo = self.lines[int(index)-1]
#            returnId.append(self.id4database[ int(lineNo[4:]) ])
#        print( '-'.join( list(map(str, returnId)) ) )
        # =============================================================
        
        
        # =======================返回给后端的id  多条=======================
#        t = time.time()
        self.result = []
        self.getManyLines(weights)
        print( ','.join(self.result) )
#        print( '算法时间:',time.time()-t,'秒' )
        # =============================================================
    


    # 返回多条线路
    def getManyLines(self, weight):
        path, pathDistance = self.dijkstra(weight, 0)
#        print(pathDistance[-1])
        if pathDistance[-1]==math.inf or len(self.result)>=5:
            return
        
        step = path[-1].split('>')
        if len(step)<=2:
            return
#        print(pathDistance[-1])
        returnId = []
        for index in step[1:-1]:
            # index表示第几条线，在lines里面找到对应的线路编号(line75)
            lineNo = self.lines[int(index)-1]
            returnId.append(self.id4database[ int(lineNo[4:]) ])
        self.result.append( '-'.join( list(map(str, returnId)) ) )

        weight[int(step[1])][int(step[2])]=math.inf
        self.getManyLines(weight)


    
    # 获取机场到终点线路
    def geta2eLine(self):
        a2eTraffic = {}
        # 先获取本地机场到对面机场的航班
#        sql = "select line_info_start,line_info_end,line_info_times,line_info_start_time,line_info_end_time,line_info_price,line_info_id from line_info where line_info_c_to_c='%s' and line_info_flag=%d"\
#        %( self.sa2eaFlag, 2 )
#        self.cursor.execute(sql)
#        tempResults = self.cursor.fetchall()
        
        tempResults = self.rd.get( self.sa2eaFlag+'_'+'2' )
        tempResults = eval(tempResults)
        
#        t = time.time()
        # 根据起始到机场线路的机场顺序排序
        results = []
        for airport in self.startAirports:
            for tr in tempResults:
                if tr[0]==airport:
                    results.append(tr)
        
        # 再获取对面机场到终点的线路
        for result in results:
            if result[0]=='衡阳南岳机场':
                continue
            #('长沙黄花国际机场', '北京首都国际机场', 7800, '007:30', '009:40', 520, 99537)
            keys = list(a2eTraffic.keys())
            if result[0]+'-'+self.endPoint not in keys:
                a2eTraffic[result[0]+'-'+self.endPoint] = {}
                
            # 如果确定了没有该本地交通，则continue
            if result[1]+'-'+self.endPoint in self.noLocalTraffic:
                continue
            
            if result[1]+'-'+self.endPoint in list(self.localTraffic.keys()):
                localRunTime = self.localTraffic[result[1]+'-'+self.endPoint]
            else:
#                sql = "select line_info_times from line_info_2 where line_info_start='%s' and line_info_end='%s'"%( result[1], self.endPoint )
#                self.cursor.execute(sql)
#                localRunTime = self.cursor.fetchone()
                localRunTime = self.rd.get(result[1]+'-'+self.endPoint)
                if localRunTime==None:
                    self.noLocalTraffic.append( result[1]+'-'+self.endPoint )
#                    print(result[1]+'-'+self.endPoint,'无此本地交通')
#                    localRunTime=math.inf
                    continue
                else:
#                    localRunTime = localRunTime[0]//60
                    localRunTime = int(localRunTime)
                self.localTraffic[result[1]+'-'+self.endPoint] = localRunTime
                
            departTime = result[3]
            startTime = time.mktime( time.strptime( self.departDate+' '+departTime[1:], '%Y-%m-%d %H:%M' ) )+int(departTime[0])*24*60*60
            endTime = startTime + result[2] + localRunTime*60
            allRunTime = (endTime-startTime)//60
            # 转换成日期格式
            startTime = time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( startTime ) )
            endTime = time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( endTime ) )
            a2eTraffic[result[0]+'-'+self.endPoint]['line'+str(self.lineIndex)] = { 'startTime':startTime, 'endTime':endTime, 'runTime':allRunTime, 'price':result[5] }
            
            self.id4database.append(result[-1])
            self.lineIndex+=1
#        print( '机场到终点线路处理数据时间:',time.time()-t )
        return a2eTraffic
    
    # 获取起点到机场线路
    def gets2aLine(self):
        s2aTraffic = {}
#        sql = "select line_info_start,line_info_end,line_info_times,line_info_start_time,line_info_end_time,line_info_price,line_info_id from line_info where line_info_c_to_c='%s' and line_info_flag=%d"\
#        %( self.s2aFlag, 1 )
#        self.cursor.execute(sql)
#        results = self.cursor.fetchall()
        
        results = self.rd.get( self.s2aFlag+'_'+'1' )
        results = eval(results)
        
#        t = time.time()
        for result in results:
            # ('衡山西站', '怀化芷江机场', 19814, '016:03', '017:47', 520, 99641)
            if result[3]==None: # 没有起始时间，可能是可乘坐本地交通直接到达 
                # TODO
                continue
            
            if result[1] not in self.startAirports:
                self.startAirports.append(result[1])
            
            if self.startPoint+'-'+result[1] not in list(s2aTraffic.keys()):
                s2aTraffic[self.startPoint+'-'+result[1]] = {}
                
            departTime = result[3]
            arriveTime = result[4]
            startTime = time.mktime( time.strptime( self.departDate+' '+departTime[1:], '%Y-%m-%d %H:%M' ) )+int(departTime[0])*24*60*60
            endTime = time.mktime( time.strptime( self.departDate+' '+arriveTime[1:], '%Y-%m-%d %H:%M' ) )+int(arriveTime[0])*24*60*60
            
            # 获取本地公交时间，更新线路起始与结束时间
            # 如果确定了没有该本地交通，则continue
            if self.startPoint+'-'+result[0] in self.noLocalTraffic:
                continue
            
            localkeys = list(self.localTraffic.keys())
            if self.startPoint+'-'+result[0] in localkeys:
                startLocalRunTime = self.localTraffic[self.startPoint+'-'+result[0]]
            else:
#                sql = "select line_info_times from line_info_2 where line_info_start='%s' and line_info_end='%s'"%( self.startPoint, result[0] )
#                self.cursor.execute(sql)
#                startLocalRunTime = self.cursor.fetchone()
                startLocalRunTime = self.rd.get(self.startPoint+'-'+result[0])
                if startLocalRunTime==None:
                    self.noLocalTraffic.append( self.startPoint+'-'+result[0] )
#                    print(self.startPoint+'-'+result[0],'无此本地交通')
#                    startLocalRunTime=math.inf
                    continue
                else:
#                    startLocalRunTime = startLocalRunTime[0]//60
                    startLocalRunTime = int(startLocalRunTime)
                self.localTraffic[self.startPoint+'-'+result[0]] = startLocalRunTime
                    
            startTime = startTime-startLocalRunTime*60-30*60
            
            allRunTime = (endTime-startTime)//60
            
            startTime = time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( startTime ) )
            endTime = time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( endTime ) )
            
            s2aTraffic[self.startPoint+'-'+result[1]]['line'+str(self.lineIndex)] = { 'startTime':startTime, 'endTime':endTime, 'runTime':allRunTime, 'price':result[5] }
            self.id4database.append(result[-1])
            self.lineIndex+=1
#        print( '起点到机场线路处理数据时间:',time.time()-t )
        return s2aTraffic
    
    
    # 获取起点到终点
    def gets2eLine(self):
        s2eTraffic = {}
        s2eTraffic[self.startPoint+'-'+self.endPoint] = {}
        
#        sql = "select line_info_start,line_info_end,line_info_times,line_info_start_time,line_info_end_time,line_info_price,count(distinct line_info_start_time,line_info_end_time),line_info_id from line_info where line_info_start='衡阳东站' and line_info_end='北京西站' and line_info_c_to_c='%s' and line_info_flag=%d group by line_info_start_time,line_info_end_time"\
#        %( self.s2eFlag, 0 )
#        self.cursor.execute(sql)
#        results = self.cursor.fetchall()
        
        results = self.rd.get( self.s2eFlag+'_'+'0' )
        results = eval(results)
        
#        t = time.time()
        for result in results:
            # ('衡阳东', '北京西', 26580, '013:30', '020:53', 520, 2)
            s2eTraffic[self.startPoint+'-'+self.endPoint]['line'+str(self.lineIndex)] = {}
            
            departTime = result[3]
            arriveTime = result[4]
            startTime = time.mktime( time.strptime( self.departDate+' '+departTime[1:], '%Y-%m-%d %H:%M' ) )+int(departTime[0])*24*60*60
            endTime = time.mktime( time.strptime( self.departDate+' '+arriveTime[1:], '%Y-%m-%d %H:%M' ) )+int(arriveTime[0])*24*60*60
            
            # 获取本地公交时间，更新线路起始与结束时间
            # 如果确定了没有该本地交通，则continue
            if self.startPoint+'-'+result[0] in self.noLocalTraffic or result[1]+'-'+self.endPoint in self.noLocalTraffic:
                continue
            
            localkeys = list(self.localTraffic.keys())
            if self.startPoint+'-'+result[0] in localkeys:
                startLocalRunTime = self.localTraffic[self.startPoint+'-'+result[0]]
            else:
#                sql = "select line_info_times from line_info_2 where line_info_start='%s' and line_info_end='%s'"%( self.startPoint, result[0] )
#                self.cursor.execute(sql)
#                startLocalRunTime = self.cursor.fetchone()
                startLocalRunTime = self.rd.get(self.startPoint+'-'+result[0])
                if startLocalRunTime==None:
                    self.noLocalTraffic.append( self.startPoint+'-'+result[0] )
#                    print(self.startPoint+'-'+result[0],'无此本地交通')
#                    startLocalRunTime=math.inf
                    continue
                else:
#                    startLocalRunTime = startLocalRunTime[0]//60
                    startLocalRunTime = int(startLocalRunTime)
#                    if self.startPoint+'-'+result[0]=='湖南工学院-衡山西站':
#                        print(startLocalRunTime,'============')
                self.localTraffic[self.startPoint+'-'+result[0]] = startLocalRunTime
                
            startTime = startTime-startLocalRunTime*60-30*60
            startTime = time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( startTime ) )
                
            if result[1]+'-'+self.endPoint in localkeys:
                endLocalRunTime = self.localTraffic[result[1]+'-'+self.endPoint]
            else:
#                sql = "select line_info_times from line_info_2 where line_info_start='%s' and line_info_end='%s'"%( result[1], self.endPoint )
#                self.cursor.execute(sql)
#                endLocalRunTime = self.cursor.fetchone()
                endLocalRunTime = self.rd.get(result[1]+'-'+self.endPoint)
                if endLocalRunTime==None:
                    self.noLocalTraffic.append( result[1]+'-'+self.endPoint )
#                    print(result[1]+'-'+self.endPoint,'无此本地交通')
#                    endLocalRunTime=math.inf
                    continue
                else:
#                    endLocalRunTime = endLocalRunTime[0]//60
                    endLocalRunTime = int(endLocalRunTime)
                self.localTraffic[result[1]+'-'+self.endPoint] = endLocalRunTime
            endTime = endTime+endLocalRunTime*60
            endTime = time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( endTime ) )
            
            
            s2eTraffic[self.startPoint+'-'+self.endPoint]['line'+str(self.lineIndex)]['startTime'] = startTime
            
            s2eTraffic[self.startPoint+'-'+self.endPoint]['line'+str(self.lineIndex)]['endTime'] = endTime
            s2eTraffic[self.startPoint+'-'+self.endPoint]['line'+str(self.lineIndex)]['runTime'] = startLocalRunTime+30+result[2]//60+endLocalRunTime
            s2eTraffic[self.startPoint+'-'+self.endPoint]['line'+str(self.lineIndex)]['price'] = result[5]
            # 把这条数据的id存入列表中
            self.id4database.append(result[-1])
            self.lineIndex += 1
#        print( '起点到终点线路处理数据时间:', time.time()-t, '秒' )
        return s2eTraffic
        
    def getWeight(self, traffic, startPoint, endPoint, startTime, startAirports, lines):
        m = math.inf
        # 权重矩阵
        weights = []
            
        #=======================起点权重=============================
        startWeight = [0]
        if startPoint+'-'+endPoint in traffic:
            # 起点直接到终点的权重
            for line in traffic[startPoint+'-'+endPoint]:
                l = traffic[startPoint+'-'+endPoint][line]
    #            print(l['startTime'])
                lStartTime = time.strptime( l['startTime'], '%Y-%m-%d %H:%M:%S' )
                if startTime>lStartTime:
                    # 如果赶不上这趟车，则权重给第二天这趟车的时间
                    time_w = (time.mktime(lStartTime)-time.mktime(startTime))/60+24*60
                else:
                    time_w = (time.mktime(lStartTime)-time.mktime(startTime))/60
                price_w = 2  # TODO 这里先默认从起点前往这条线路的价格为2
                # 根据用户需求选择出行权重
                if self.requirement=='1':
                    w = time_w*1 + price_w*0
                elif self.requirement=='2':
                    w = time_w*0 + price_w*1
                elif self.requirement=='1,2':
                    w = time_w*0.5 + price_w*0.5
                else:
                    w = time_w
                startWeight.append( w )
        # 起点到机场线路的权重
        for airport in startAirports:
            for line in traffic[startPoint+'-'+airport]:
                l = traffic[startPoint+'-'+airport][line]
                lStartTime = time.strptime( l['startTime'], '%Y-%m-%d %H:%M:%S' )
                if startTime>lStartTime:
                    # 如果赶不上这趟车，则权重给第二天这趟车的时间
                    time_w = (time.mktime(lStartTime)-time.mktime(startTime))/60+24*60
                else:
                    time_w = (time.mktime(lStartTime)-time.mktime(startTime))/60
                price_w = 2  # TODO 这里先默认从起点前往这条线路的价格为2
                # 根据用户需求选择出行权重
                if self.requirement=='1':
                    w = time_w*1 + price_w*0
                elif self.requirement=='2':
                    w = time_w*0 + price_w*1
                elif self.requirement=='1,2':
                    w = time_w*0.5 + price_w*0.5
                else:
                    w = time_w
                startWeight.append(w)
        # 机场到终点的权重
        for airport in startAirports:
            for line in traffic[airport+'-'+endPoint]:
                startWeight.append(m)
        startWeight.append(m)
        weights.append( startWeight )
        
        #=======================起点直接到终点线路权重=============================
        if startPoint+'-'+endPoint in traffic:
            for line in traffic[startPoint+'-'+endPoint]:
                s2eWeight = []
                s2eWeight.append( weights[len(s2eWeight)][len(weights)] )
                for line2 in traffic[startPoint+'-'+endPoint]:
                    if line==line2:
                        s2eWeight.append(0)
                    elif lines.index(line2)<lines.index(line):
                        s2eWeight.append( weights[len(s2eWeight)][len(weights)] )
                    else:
                        s2eWeight.append(m)
                for airport in startAirports:
                    for line2 in traffic[startPoint+'-'+airport]:
                        s2eWeight.append(m)
                for airport in startAirports:
                    for line2 in traffic[airport+'-'+endPoint]: 
                        s2eWeight.append(m)
                
                time_w = float( traffic[startPoint+'-'+endPoint][line]['runTime'] )
                price_w = traffic[startPoint+'-'+endPoint][line]['price'] + 2  # TODO 这里先默认终点结束这条线路的价格为2
                # 根据用户需求选择出行权重
                if self.requirement=='1':
                    w = time_w*1 + price_w*0
                elif self.requirement=='2':
                    w = time_w*0 + price_w*1
                elif self.requirement=='1,2':
                    w = time_w*0.5 + price_w*0.5
                else:
                    w = time_w
                
                s2eWeight.append( w )
                weights.append( s2eWeight )
        
        #=======================起点到机场线路权重=============================
        for airport in startAirports:
            for line in traffic[startPoint+'-'+airport]:
                s2aWeight = []
                s2aWeight.append( weights[0][len(weights)] )
                if startPoint+'-'+endPoint in traffic:
                    for line2 in traffic[startPoint+'-'+endPoint]:
                        s2aWeight.append(m)
                for airport2 in startAirports:
                    for line2 in traffic[startPoint+'-'+airport2]:
                        if line==line2:
                            s2aWeight.append(0)
                        elif lines.index(line2)<lines.index(line):
                            s2aWeight.append(m)
                        else:
                            s2aWeight.append(m)
                for airport2 in startAirports:
                    for line2 in traffic[airport2+'-'+endPoint]:
                        if airport==airport2:
                            runTime = float(traffic[startPoint+'-'+airport][line]['runTime'])
                            endTime = time.strptime( traffic[startPoint+'-'+airport][line]['endTime'], '%Y-%m-%d %H:%M:%S' )
                            startTime = time.strptime( traffic[airport+'-'+endPoint][line2]['startTime'], '%Y-%m-%d %H:%M:%S' )
                            if endTime>startTime:
                                s2aWeight.append(m)
                            else:
                                time_w = runTime+(time.mktime(startTime)-time.mktime(endTime))/60
                                price_w = traffic[startPoint+'-'+airport][line]['price']
                                # 根据用户需求选择出行权重
                                if self.requirement=='1':
                                    w = time_w*1 + price_w*0
                                elif self.requirement=='2':
                                    w = time_w*0 + price_w*1
                                elif self.requirement=='1,2':
                                    w = time_w*0.5 + price_w*0.5
                                else:
                                    w = time_w
                                s2aWeight.append( w )
                        else:
                            s2aWeight.append(m)
                s2aWeight.append(m)
                weights.append(s2aWeight)
                
#        print('weights', len(weights))
#        for w in weights:
#            print(len(w))
        # 171,200
        #=======================机场到终点线路权重=============================
        for airport in startAirports:
            for line in traffic[airport+'-'+endPoint]:
                a2eWeight = []
                a2eWeight.append( weights[0][len(weights)] )
#                print(weights[0][len(weights)])
                for line2 in lines:
                    if line2==line:
                        a2eWeight.append(0)
                    elif lines.index(line2)<lines.index(line):
                        a2eWeight.append( weights[len(a2eWeight)][len(weights)] )
                    else:
                        a2eWeight.append(m)
                
                time_w = float(traffic[airport+'-'+endPoint][line]['runTime'])
                price_w = traffic[airport+'-'+endPoint][line]['price'] + 2 # TODO 这里先默认终点结束这条线路的价格为2
                # 根据用户需求选择出行权重
                if self.requirement=='1':
                    w = time_w*1 + price_w*0
                elif self.requirement=='2':
                    w = time_w*0 + price_w*1
                elif self.requirement=='1,2':
                    w = time_w*0.5 + price_w*0.5
                else:
                    w = time_w
                
                a2eWeight.append( w )
                weights.append(a2eWeight)
        
        #=======================终点权重=============================
        endWeight = []
        for w in weights:
            endWeight.append( w[-1] )
        endWeight.append(0)
        weights.append(endWeight)
        
        return weights
        
        
        
    def dijkstra(self, weight, start):
        '''
        weight:有权图的权重矩阵
        start:起点编号
        '''
        weight2 = copy.deepcopy( weight ) # 避免第二次调用时改变了weight
        n = len( weight2 )   # 顶点个数，对应地点的数量
        pathDistance = np.zeros( (n) )   # 保存从起点到其它点的最短距离  初始化[0. 0. 0. 0. 0.]
        path = []   # 保存从起点到其它点最短路径的走法
        for i in range( n ):
            path.append( str(start)+'>'+str(i) )
        visited = np.zeros( (n) )   # 标记该点的最短路径是否已求出  0表示没有  初始化[0. 0. 0. 0. 0.]
        # 初始化第一个点是已经求出的  即：自身点到自身点的距离
        visited[start] = 1
        pathDistance[start] = 0
        
        for m in range(1,n):    # 加入n-1个地点
            k = -1   # 用来记录离start最近的未标记的点
            dmin = math.inf    # 用来记录离start最近的未标记的点的距离
            for i in range(n):
                if visited[i]==0 and weight2[start][i]<dmin:
                    dmin = weight2[start][i]
                    k = i
            # 上面这个循环即找到了离start最近的点以及距离
            # 将新选出的点标记为已求出的最短路径，且到start的最短距离即为dmin
            pathDistance[k] = dmin
            visited[k] = 1
            
            # 以k为中间点，更新从start到未访问的点的距离
            for i in range(n):
                # 如果 '起始点到当前点距离' + '当前点到某点距离' < '起始点到某点距离', 则更新
                if visited[i]==0 and weight2[start][k]+weight2[k][i]<weight2[start][i]:
                    weight2[start][i] = weight2[start][k]+weight2[k][i]
                    path[i] = path[k]+'>'+str(i)
                    
        return path, pathDistance
        
if __name__=='__main__':
#    t = time.time()
    try:
        getLine()
    except Exception as e:
        print(e)
#    print( '用时：',time.time()-t,'秒' )