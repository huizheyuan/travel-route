let server='';// 用户
let serverLong='';// 长途
let serverShort='';// 短途

if(process.env.NODE_ENV=='development'){
  server='http://localhost:80/';
  serverLong='http://localhost:65525/';
  serverShort='http://localhost:65526/';
}else{
  server='http://localhost:80/';
  serverLong='http://localhost:65525/';
  serverShort='http://localhost:65526/';
}

export const SERVER=server;
export const SERVERLONG=serverLong;
export const SERVERSHORT=serverShort;
