declare module 'react-simple-maps' {
  import { ComponentType, ReactNode } from 'react';

  export interface ComposableMapProps {
    projection?: string;
    projectionConfig?: {
      scale?: number;
      center?: [number, number];
      [key: string]: any;
    };
    width?: number;
    height?: number;
    className?: string;
    style?: React.CSSProperties;
    children?: ReactNode;
  }

  export interface Geography {
    rsmKey: string;
    properties: {
      name: string;
      [key: string]: any;
    };
    [key: string]: any;
  }

  export interface GeographiesProps {
    geography: string | object;
    children: (props: { geographies: Geography[] }) => ReactNode;
  }

  export interface GeographyProps {
    geography: Geography;
    style?: {
      default?: React.CSSProperties;
      hover?: React.CSSProperties;
      pressed?: React.CSSProperties;
    };
    onClick?: () => void;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    [key: string]: any;
  }

  export const ComposableMap: ComponentType<ComposableMapProps>;
  export const Geographies: ComponentType<GeographiesProps>;
  export const Geography: ComponentType<GeographyProps>;
}
























