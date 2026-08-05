import React from 'react';import {Easing,interpolate,useCurrentFrame} from 'remotion';
export const Subtitle:React.FC<{text:string;dark?:boolean}>=({text})=>{
  const frame=useCurrentFrame();
  const reveal=interpolate(frame,[5,18],[0,1],{easing:Easing.out(Easing.back(1.2)),extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const highlight=interpolate(frame,[10,28],[0,100],{easing:Easing.inOut(Easing.cubic),extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <div style={{fontSize:48,lineHeight:1.35,fontWeight:700,color:'white',textAlign:'center',WebkitTextStroke:'1.5px #000',paintOrder:'stroke fill',textShadow:'0 4px 5px rgba(0,0,0,.9),0 10px 24px rgba(0,0,0,.45)',opacity:reveal,transform:`translate3d(0,${(1-reveal)*26}px,0) scale(${.96+reveal*.04})`}}><span style={{padding:'3px 10px 7px',backgroundImage:'linear-gradient(90deg,rgba(230,62,55,.88),rgba(230,62,55,.88))',backgroundRepeat:'no-repeat',backgroundPosition:'left 88%',backgroundSize:`${highlight}% 34%`}}>{text}</span></div>;
};
