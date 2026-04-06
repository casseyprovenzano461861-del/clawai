import React, { useState, useEffect, useRef } from 'react';
import { Image as ImageIcon } from 'lucide-react';

export interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  placeholder?: React.ReactNode;
  errorFallback?: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
  onLoad?: () => void;
  onError?: () => void;
  blurDataURL?: string;
  priority?: boolean;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder,
  errorFallback,
  threshold = 0.1,
  rootMargin = '50px',
  onLoad,
  onError,
  blurDataURL,
  priority = false,
  className = '',
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isInView, setIsInView] = useState(priority);
  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // 默认占位符
  const defaultPlaceholder = (
    <div className="flex items-center justify-center w-full h-full bg-gray-100 dark:bg-gray-800">
      <ImageIcon className="h-8 w-8 text-gray-400" />
    </div>
  );

  // 默认错误回退
  const defaultErrorFallback = (
    <div className="flex items-center justify-center w-full h-full bg-gray-100 dark:bg-gray-800">
      <div className="text-center">
        <ImageIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-500">图片加载失败</p>
      </div>
    </div>
  );

  // 设置Intersection Observer
  useEffect(() => {
    if (priority || !imgRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold,
        rootMargin,
      }
    );

    observer.observe(imgRef.current);
    observerRef.current = observer;

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [priority, threshold, rootMargin]);

  // 处理图片加载
  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  // 处理图片错误
  const handleError = () => {
    setIsError(true);
    onError?.();
  };

  // 如果图片在视图中或优先级加载，则加载图片
  const shouldLoadImage = isInView || priority;

  return (
    <div className="relative overflow-hidden" ref={imgRef}>
      {/* 占位符 */}
      {!isLoaded && !isError && (
        <div className="absolute inset-0">
          {placeholder || defaultPlaceholder}
        </div>
      )}

      {/* 错误回退 */}
      {isError && (
        <div className="absolute inset-0">
          {errorFallback || defaultErrorFallback}
        </div>
      )}

      {/* 实际图片 */}
      {shouldLoadImage && !isError && (
        <>
          {/* 模糊预览 */}
          {blurDataURL && !isLoaded && (
            <img
              src={blurDataURL}
              alt={`${alt} (预览)`}
              className={`absolute inset-0 w-full h-full object-cover filter blur-sm ${className}`}
              {...props}
            />
          )}

          {/* 实际图片 */}
          <img
            src={src}
            alt={alt}
            className={`
              w-full h-full object-cover
              transition-opacity duration-300
              ${isLoaded ? 'opacity-100' : 'opacity-0'}
              ${className}
            `}
            onLoad={handleLoad}
            onError={handleError}
            loading={priority ? 'eager' : 'lazy'}
            {...props}
          />
        </>
      )}

      {/* 加载指示器 */}
      {shouldLoadImage && !isLoaded && !isError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800 bg-opacity-50">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
      )}
    </div>
  );
};

// 响应式图片组件
export interface ResponsiveImageProps extends LazyImageProps {
  sizes?: string;
  srcSet?: string;
  breakpoints?: {
    [key: string]: string;
  };
}

export const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  sizes = '100vw',
  srcSet,
  breakpoints,
  ...props
}) => {
  // 根据断点生成srcSet
  const generateSrcSet = () => {
    if (srcSet) return srcSet;
    
    if (breakpoints) {
      return Object.entries(breakpoints)
        .map(([width, url]) => `${url} ${width}w`)
        .join(', ');
    }
    
    return undefined;
  };

  return (
    <LazyImage
      srcSet={generateSrcSet()}
      sizes={sizes}
      {...props}
    />
  );
};

// 图片画廊组件
export interface ImageGalleryProps {
  images: Array<{
    src: string;
    alt: string;
    caption?: string;
  }>;
  columns?: number;
  gap?: number;
  aspectRatio?: string;
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images,
  columns = 3,
  gap = 4,
  aspectRatio = '16/9',
}) => {
  const gridTemplateColumns = `repeat(${columns}, 1fr)`;

  return (
    <div
      className="grid"
      style={{
        gridTemplateColumns,
        gap: `${gap * 0.25}rem`,
      }}
    >
      {images.map((image, index) => (
        <div
          key={index}
          className="relative overflow-hidden rounded-lg"
          style={{ aspectRatio }}
        >
          <LazyImage
            src={image.src}
            alt={image.alt}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
          />
          
          {image.caption && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
              <p className="text-white text-sm">{image.caption}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default LazyImage;