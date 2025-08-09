"use client";
export function VideoPlayer({ src, vttSrc }: { src: string; vttSrc?: string }){
  return (
    <video controls className="w-full rounded-xl overflow-hidden">
      <source src={src} type="video/mp4" />
      {vttSrc && <track kind="subtitles" srcLang="en" src={vttSrc} default />}
      Your browser does not support the video tag.
    </video>
  );
}
