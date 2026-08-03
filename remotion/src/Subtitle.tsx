import React from 'react';
export const Subtitle:React.FC<{text:string;dark?:boolean}>=({text,dark=true})=><div style={{fontSize:48,lineHeight:1.35,fontWeight:700,color:dark?'white':'#171717',textAlign:'center',textShadow:dark?'0 3px 12px #000':'none'}}>{text}</div>;
