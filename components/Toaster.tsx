'use client';

import { Toaster as SonnerToaster } from 'sonner';

export default function Toaster() {
  return (
    <SonnerToaster
      position="top-right"
      theme="light"
      richColors
      closeButton
      duration={4000}
    />
  );
}

