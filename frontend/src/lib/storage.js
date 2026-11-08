export const KEY='research-bridge-react-v1';
export function load(){try{return JSON.parse(localStorage.getItem(KEY))||{submissions:[],notifications:[]};}catch{return {submissions:[],notifications:[]};}}
export function persist(data){localStorage.setItem(KEY,JSON.stringify(data));}
function db(){return new Promise((resolve,reject)=>{const req=indexedDB.open('research-bridge-files',1);req.onupgradeneeded=()=>req.result.createObjectStore('files');req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});}
export async function storeFile(key,file){const d=await db();try{await new Promise((resolve,reject)=>{const tx=d.transaction('files','readwrite');tx.objectStore('files').put(file,key);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);});}finally{d.close();}}
export async function readFile(key){const d=await db();try{return await new Promise((resolve,reject)=>{const r=d.transaction('files').objectStore('files').get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}finally{d.close();}}
export async function deleteFile(key){const d=await db();try{await new Promise((resolve,reject)=>{const tx=d.transaction('files','readwrite');tx.objectStore('files').delete(key);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error);});}finally{d.close();}}
