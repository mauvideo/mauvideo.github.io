import React from 'react';
import {AbsoluteFill,Easing,Img,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';

const MOTIONS=['zoom-in','zoom-out','pan-left','pan-right','pan-up','pan-down','ken-burns','dolly-zoom','slow-drift'] as const;
const easeProgress=(frame:number,duration:number)=>interpolate(frame,[0,Math.max(1,duration-1)],[0,1],{easing:Easing.inOut(Easing.cubic),extrapolateLeft:'clamp',extrapolateRight:'clamp'});

export const Photo:React.FC<{path:string;radius?:number;variant?:number;sceneId?:number}>=({path,radius=24,variant=0,sceneId=0})=>{
  const frame=useCurrentFrame(),{durationInFrames}=useVideoConfig(),progress=easeProgress(frame,durationInFrames);
  // Stable pseudo-random selection makes parallel renders reproducible.
  const motion=MOTIONS[Math.abs(sceneId*sceneId*31+variant*17)%MOTIONS.length];
  let x=0,y=0,scale=1.1;
  switch(motion){
    case'zoom-in':scale=1.02+progress*.14;break;case'zoom-out':scale=1.17-progress*.14;break;
    case'pan-left':x=5-progress*10;scale=1.12;break;case'pan-right':x=-5+progress*10;scale=1.12;break;
    case'pan-up':y=5-progress*10;scale=1.12;break;case'pan-down':y=-5+progress*10;scale=1.12;break;
    case'ken-burns':x=-4+progress*8;y=3-progress*6;scale=1.04+progress*.12;break;
    case'dolly-zoom':x=(progress-.5)*2;scale=1.18-progress*.12;break;
    case'slow-drift':x=-2+progress*4;y=-1+progress*2;scale=1.07+progress*.03;break;
  }
  return <Img src={staticFile(path.replace(/^\.\//,''))} style={{width:'100%',height:'100%',objectFit:'cover',objectPosition:variant%2?'65% center':'35% center',borderRadius:radius,transform:`translate3d(${x}%,${y}%,0) scale(${scale})`,willChange:'transform'}}/>;
};

const transitionStyle=(kind:number,p:number):React.CSSProperties=>{
  if(kind===0)return{opacity:p}; // Cross Fade
  if(kind===1)return{opacity:p,filter:`blur(${(1-p)*14}px)`}; // Blur
  if(kind===2)return{transform:`translate3d(${(1-p)*100}%,0,0)`}; // Slide
  return{opacity:p,backgroundColor:`rgba(255,255,255,${1-p})`}; // Flash
};

export const SceneEffects:React.FC<{seed:number;children:React.ReactNode}>=({seed,children})=>{
  const frame=useCurrentFrame(),transition=interpolate(frame,[0,12],[0,1],{easing:Easing.out(Easing.cubic),extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  return <AbsoluteFill style={{...transitionStyle(Math.abs(seed)%4,transition),overflow:'hidden'}}>{children}
    <AbsoluteFill style={{pointerEvents:'none',background:'linear-gradient(115deg,rgba(255,180,90,.035),transparent 45%,rgba(70,120,255,.045))'}}/>
    <AbsoluteFill style={{pointerEvents:'none',background:'radial-gradient(circle,transparent 52%,rgba(0,0,0,.32) 100%)'}}/>
    <AbsoluteFill style={{pointerEvents:'none',opacity:.075,backgroundImage:'url("data:image/svg+xml,%3Csvg viewBox=%270 0 180 180%27 xmlns=%27http://www.w3.org/2000/svg%27%3E%3Cfilter id=%27n%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%27.85%27 numOctaves=%272%27 stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23n)%27 opacity=%27.45%27/%3E%3C/svg%3E")',mixBlendMode:'soft-light'}}/>
  </AbsoluteFill>;
};
