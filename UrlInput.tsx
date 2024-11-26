'use client'

import { useState } from 'react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

interface UrlInputProps {
  onSubmit: (url: string) => void
}

export default function UrlInput({ onSubmit }: UrlInputProps) {
  const [url, setUrl] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(url)
  }

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <Input
        type="url"
        placeholder="https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="flex-grow"
      />
      <Button type="submit">抽出</Button>
    </form>
  )
}

