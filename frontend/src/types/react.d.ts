import * as React from 'react';

declare global {
  const React: typeof import('react');
  namespace React {
    export = React;
  }
} 