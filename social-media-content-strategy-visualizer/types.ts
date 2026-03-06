
export enum SocialPlatform {
  YouTube = 'YouTube',
  LinkedIn = 'LinkedIn',
  X = 'X',
  Reddit = 'Reddit',
  Instagram = 'Instagram',
}

export interface NodeData {
  id: string;
  platform: SocialPlatform;
  content: string;
  x: number;
  y: number;
  width: number;
  height: number;
  thumbnailUrl?: string;
}

export interface EdgeData {
  id:string;
  from: string;
  to: string;
}

export interface Point {
  x: number;
  y: number;
}
