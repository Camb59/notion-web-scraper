'use client'

import { useState } from 'react'
import { Calendar, Link2 } from 'lucide-react'
import { cn } from "@/lib/utils"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

interface ContentPreviewProps {
  content: {
    title: string
    body: string
    url: string
    date: string
  }
  onTranslate: () => Promise<{ title: string; body: string }>
}

export default function ContentPreview({ content, onTranslate }: ContentPreviewProps) {
  const [viewMode, setViewMode] = useState<'original' | 'translated' | 'both'>('original')
  const [isTranslated, setIsTranslated] = useState(false)
  const [translatedContent, setTranslatedContent] = useState<{
    title: string;
    body: string;
  } | null>(null)

  const handleTabChange = async (value: string) => {
    if ((value === 'translated' || value === 'both') && !isTranslated) {
      const translated = await onTranslate()
      setTranslatedContent(translated)
      setIsTranslated(true)
    }
    setViewMode(value as 'original' | 'translated' | 'both')
  }

  const renderContent = (content: { title: string; body: string }, isTranslated: boolean) => {
    return (
      <article className="space-y-6">
        <h1 className="text-[2.5rem] font-bold leading-tight tracking-tight">
          {content.title}
        </h1>
        <div className="flex items-center gap-6 text-base text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            <span>{content.date}</span>
          </div>
          <div className="flex items-center gap-2">
            <Link2 className="h-5 w-5" />
            <a href={content.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
              ソース
            </a>
          </div>
        </div>
        <div className="prose prose-lg max-w-none prose-headings:font-bold prose-headings:tracking-tight prose-img:rounded-lg prose-img:shadow-lg">
          <div dangerouslySetInnerHTML={{ __html: content.body }} />
        </div>
      </article>
    )
  }

  return (
    <div className="space-y-6">
      <Tabs value={viewMode} onValueChange={handleTabChange} className="w-full">
        <div className="flex justify-center mb-6">
          <TabsList>
            <TabsTrigger value="original">原文</TabsTrigger>
            <TabsTrigger value="translated">翻訳文</TabsTrigger>
            <TabsTrigger value="both">翻訳文｜原文</TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="original" className="mt-6">
          {renderContent(content, false)}
        </TabsContent>
        <TabsContent value="translated" className="mt-6">
          {isTranslated && translatedContent ? (
            renderContent(translatedContent, true)
          ) : (
            <div className="py-8 text-center text-muted-foreground">
              翻訳中...
            </div>
          )}
        </TabsContent>
        <TabsContent value="both" className="mt-6">
          <div className="grid grid-cols-2 gap-8">
            <div className="border-r pr-8">
              {renderContent(content, false)}
            </div>
            <div className="pl-8">
              {isTranslated && translatedContent ? (
                renderContent(translatedContent, true)
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  翻訳中...
                </div>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

