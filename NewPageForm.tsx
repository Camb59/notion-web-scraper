'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface NewPageFormProps {
  onSubmit: (data: any) => void
  properties: Record<string, string>
}

export default function NewPageForm({ onSubmit, properties }: NewPageFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    const data = Object.fromEntries(formData)
    onSubmit(data)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {Object.entries(properties).map(([key, type]) => (
        <div key={key} className="space-y-2">
          <Label htmlFor={key}>{key}</Label>
          {type === 'rich_text' ? (
            <Textarea
              id={key}
              name={key}
              rows={5}
              className="resize-none"
            />
          ) : (
            <Input 
              id={key} 
              name={key} 
              type={type === 'date' ? 'date' : 'text'} 
            />
          )}
        </div>
      ))}

      <Button type="submit" className="w-full">
        ページを作成
      </Button>
    </form>
  )
}

