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
      <article className="w-full">
        <h1 className="text-[2.5rem] font-bold leading-tight tracking-tight mb-6">
          {content.title}
        </h1>
        <div className="w-full">
          <div 
            dangerouslySetInnerHTML={{ __html: content.body }}
            className={cn(
              "w-full",
              "[&_img]:w-full [&_img]:h-auto [&_img]:object-contain",
              "[&_figure]:w-full [&_figure]:my-4",
              "[&_figure_img]:w-full [&_figure_img]:h-auto [&_figure_img]:object-contain",
              "[&_table]:w-full [&_table]:border-collapse [&_table]:my-4",
              "[&_td]:border [&_td]:p-2 [&_th]:border [&_th]:p-2",
              "[&_h1]:text-4xl [&_h1]:font-bold [&_h1]:mb-4",
              "[&_h2]:text-3xl [&_h2]:font-bold [&_h2]:mb-3",
              "[&_h3]:text-2xl [&_h3]:font-bold [&_h2]:mb-2",
              "[&_p]:mb-4",
              "[&_ul]:mb-4",
              "[&_ol]:mb-4",
              "[&_li]:ml-4"
            )}
          />
        </div>
      </article>
    )
  }

  return (
    <div className="w-full">
      <Tabs value={viewMode} onValueChange={handleTabChange}>
        <div className="flex justify-center mb-6">
          <TabsList>
            <TabsTrigger value="original">原文</TabsTrigger>
            <TabsTrigger value="translated">翻訳文</TabsTrigger>
            <TabsTrigger value="both">翻訳文｜原文</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="original">
          <div className="w-full">
            {renderContent(content, false)}
          </div>
        </TabsContent>

        <TabsContent value="translated">
          <div className="w-full">
            {isTranslated && translatedContent ? (
              renderContent(translatedContent, true)
            ) : (
              <div className="py-8 text-center text-muted-foreground">
                翻訳中...
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="both">
          <div className="flex flex-col w-full">
            <div className="w-full mb-8">
              {renderContent(content, false)}
            </div>
            <div className="w-full">
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
