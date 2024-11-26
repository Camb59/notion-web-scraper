'use client'

import { useState } from 'react'
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import UrlInput from '@/components/UrlInput'
import ContentPreview from '@/components/ContentPreview'
import NotionPropertiesSelector from '@/components/NotionPropertiesSelector'

// モックデータ（実際の実装では削除してください）
const mockScrapedContent = {
  title: "サンプルタイトル",
  body: "<p>これはサンプルの本文です。</p><p>複数の段落があります。</p>",
}

const mockNotionProperties = [
  { id: "title", name: "タイトル", type: "title" },
  { id: "body", name: "本文", type: "rich_text" },
  { id: "url", name: "URL", type: "url" },
  { id: "date", name: "日付", type: "date" },
]

export default function Home() {
  const { toast } = useToast()
  const [scrapedContent, setScrapedContent] = useState(mockScrapedContent)
  const [isTranslated, setIsTranslated] = useState(false)
  const [notionProperties, setNotionProperties] = useState<Record<string, string>>({})

  const handleUrlSubmit = async (url: string) => {
    // ここで実際のスクレイピングを行います
    console.log("Scraping URL:", url)
    // モックデータを使用（実際の実装では削除してください）
    setScrapedContent(mockScrapedContent)
    toast({
      title: "コンテンツ抽出完了",
      description: "Webページの内容を抽出しました。",
    })
  }

  const handleTranslate = async () => {
    // ここで実際の翻訳を行います
    console.log("Translating content")
    // モックの翻訳（実際の実装では削除してください）
    setScrapedContent(prev => ({
      ...prev,
      translatedTitle: "Translated: " + prev.title,
      translatedBody: "<p>This is a translated sample body.</p><p>It has multiple paragraphs.</p>",
    }))
    setIsTranslated(true)
    toast({
      title: "翻訳完了",
      description: "コンテンツを翻訳しました。",
    })
  }

  const handlePropertyChange = (propertyId: string, value: string) => {
    setNotionProperties(prev => ({ ...prev, [propertyId]: value }))
  }

  const handleCreateNotionPage = async () => {
    // ここでNotionページを作成します
    console.log("Creating Notion page with properties:", notionProperties)
    // NotionAPIを呼び出してページを作成（実際の実装が必要です）
    toast({
      title: "Notionページ作成完了",
      description: "新しいNotionページが作成されました。",
    })
  }

  return (
    <div className="w-full max-w-none p-4">
      <h1 className="text-3xl font-bold text-center mb-6">Notion Web Scraper</h1>
      <div className="flex flex-col lg:flex-row gap-6 w-full max-w-none">
        <div className="flex-1 w-full max-w-none space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>URLを入力</CardTitle>
            </CardHeader>
            <CardContent>
              <UrlInput onSubmit={handleUrlSubmit} />
            </CardContent>
          </Card>
          {scrapedContent && (
            <Card className="w-full max-w-none">
              <CardContent>
                <div className="text-xs text-muted-foreground mb-2">コンテンツプレビュー</div>
                <ContentPreview content={scrapedContent} onTranslate={handleTranslate} />
              </CardContent>
            </Card>
          )}
        </div>
        <div className="w-full lg:w-80 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>プロパティ</CardTitle>
            </CardHeader>
            <CardContent>
              <NotionPropertiesSelector
                properties={mockNotionProperties}
                onPropertyChange={handlePropertyChange}
              />
            </CardContent>
          </Card>
          <Button onClick={handleCreateNotionPage} className="w-full">
            Notionページを作成
          </Button>
        </div>
      </div>
      <Toaster />
    </div>
  )
}

