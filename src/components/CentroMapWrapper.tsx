'use client'

import dynamic from 'next/dynamic'
import type { CentroMapProps } from './CentroMap'

const CentroMap = dynamic(() => import('./CentroMap'), { ssr: false })

export default function CentroMapWrapper(props: CentroMapProps) {
  return <CentroMap {...props} />
}
