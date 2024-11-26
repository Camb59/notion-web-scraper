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
        <div className="flex items-center gap-6 text-base text-muted-foreground mb-6">
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
        <div className="prose prose-lg w-full max-w-none">
          <div 
            dangerouslySetInnerHTML={{ __html: content.body }}
            className={cn(
              "w-full overflow-x-hidden",
              "[&_img]:w-full [&_img]:max-w-full [&_img]:h-auto [&_img]:object-contain [&_img]:mx-auto",
              "[&_figure]:w-full [&_figure]:my-4 [&_figure]:overflow-hidden",
              "[&_figure_img]:max-w-full [&_figure_img]:h-auto [&_figure_img]:object-contain [&_figure_img]:mx-auto",
              "[&_table]:w-full [&_table]:border-collapse [&_table]:my-4 [&_table]:table-auto",
              "[&_td]:border [&_td]:p-2 [&_th]:border [&_th]:p-2 [&_th]:bg-muted",
              "[&_h1]:text-4xl [&_h1]:font-bold [&_h1]:mb-4",
              "[&_h2]:text-3xl [&_h2]:font-bold [&_h2]:mb-3",
              "[&_h3]:text-2xl [&_h3]:font-bold [&_h3]:mb-2",
              "[&_p]:mb-4 [&_ul]:mb-4 [&_ol]:mb-4",
              "[&_li]:ml-4",
              "[&_pre]:bg-muted [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto",
              "[&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded",
              "[&_blockquote]:border-l-4 [&_blockquote]:border-muted [&_blockquote]:pl-4 [&_blockquote]:italic"
            )}
          />
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
          <div className="w-full">
            {renderContent(content, false)}
          </div>
        </TabsContent>
        <TabsContent value="translated" className="mt-6">
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
        <TabsContent value="both" className="mt-6">
          <div className="w-full space-y-12">
            <div className="w-full">
              {renderContent(content, false)}
            </div>
            <div className="w-full pt-8 border-t">
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
