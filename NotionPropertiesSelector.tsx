'use client'

import { useState, useEffect } from 'react'
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import { Calendar, GripVertical } from 'lucide-react'
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon } from "@radix-ui/react-icons"
import { format } from "date-fns"
import { Calendar } from "@/components/ui/calendar"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils" //this line was added

interface NotionProperty {
  id: string
  name: string
  type: string
  options?: { label: string; value: string }[]
  database_id?: string
  database_title?: string
}

interface NotionPropertiesSelectorProps {
  onPropertyChange: (propertyId: string, value: string) => void
}

const NOTION_PROPERTIES: NotionProperty[] = [
  {
    id: 'createdAt',
    name: '作成日',
    type: 'created_time',
  },
  {
    id: 'date',
    name: '日付',
    type: 'date',
  },
  {
    id: 'nature',
    name: '性質',
    type: 'select',
    options: [
      { label: '技術', value: 'technical' },
      { label: 'ビジネス', value: 'business' },
      { label: '法律', value: 'legal' },
    ]
  },
  {
    id: 'tags',
    name: 'タグ',
    type: 'multi_select',
    options: [
      { label: 'Web', value: 'web' },
      { label: 'AI', value: 'ai' },
      { label: 'デザイン', value: 'design' },
    ]
  },
  {
    id: 'mainCategory',
    name: 'MainCategory',
    type: 'select',
    options: [
      { label: '開発', value: 'development' },
      { label: 'マーケティング', value: 'marketing' },
      { label: '経営', value: 'management' },
    ]
  },
  {
    id: 'subCategory',
    name: 'SubCategory',
    type: 'select',
    options: [
      { label: 'フロントエンド', value: 'frontend' },
      { label: 'バックエンド', value: 'backend' },
      { label: 'インフラ', value: 'infrastructure' },
    ]
  },
  {
    id: 'importance',
    name: '重要度',
    type: 'select',
    options: [
      { label: '高', value: 'high' },
      { label: '中', value: 'medium' },
      { label: '低', value: 'low' },
    ]
  },
]

export default function NotionPropertiesSelector({ onPropertyChange }: NotionPropertiesSelectorProps) {
  const [properties, setProperties] = useState(NOTION_PROPERTIES)
  const [selectedValues, setSelectedValues] = useState<Record<string, any>>({})

  useEffect(() => {
    // Set current time for creation date
    const now = new Date()
    setSelectedValues(prev => ({
      ...prev,
      createdAt: now.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
      date: now.toISOString().split('T')[0]
    }))

    // Fetch Notion properties from API
    fetchNotionProperties()
  }, [])

  const fetchNotionProperties = async () => {
    try {
      const response = await fetch('/api/notion/properties')
      if (!response.ok) throw new Error('Failed to fetch Notion properties')
      const data = await response.json()
      if (data.status === 'success') {
        setProperties(Object.values(data.data))
      }
    } catch (error) {
      console.error('Error fetching Notion properties:', error)
    }
  }

  const handleDragEnd = (result: any) => {
    if (!result.destination) return

    const items = Array.from(properties)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    setProperties(items)
  }

  const handlePropertyChange = (propertyId: string, value: string | Date) => {
    const property = properties.find(p => p.id === propertyId)
    if (!property) return

    let formattedValue: any
    switch (property.type) {
      case 'date':
        formattedValue = {
          date: {
            start: value instanceof Date ? value.toISOString() : value
          }
        }
        break
      case 'select':
        formattedValue = {
          select: {
            name: value
          }
        }
        break
      case 'multi_select':
        formattedValue = {
          multi_select: value.split(',').map(v => ({ name: v.trim() }))
        }
        break
      case 'url':
        formattedValue = {
          url: value
        }
        break
      case 'title':
        formattedValue = {
          title: [{ text: { content: value } }]
        }
        break
      case 'rich_text':
        formattedValue = {
          rich_text: [{ text: { content: value } }]
        }
        break
      default:
        formattedValue = value
    }

    setSelectedValues(prev => ({ ...prev, [propertyId]: formattedValue }))
    onPropertyChange(propertyId, formattedValue)
  }

  return (
    <ScrollArea className="h-[calc(100vh-200px)]">
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="properties">
          {(provided) => (
            <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-4">
              {properties.map((property, index) => (
                <Draggable key={property.id} draggableId={property.id} index={index}>
                  {(provided) => (
                    <Card
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      className="bg-background"
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2">
                          <div {...provided.dragHandleProps}>
                            <GripVertical className="h-5 w-5 text-muted-foreground" />
                          </div>
                          <div className="flex-1 space-y-2">
                            <Label className="text-sm font-medium">
                              {property.name}
                            </Label>
                            {property.id === 'createdAt' ? (
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Calendar className="h-4 w-4" />
                                {selectedValues.createdAt}
                              </div>
                            ) : property.id === 'date' ? (
                              <Popover>
                                <PopoverTrigger asChild>
                                  <Button
                                    variant={"outline"}
                                    className={cn(
                                      "w-full justify-start text-left font-normal",
                                      !selectedValues[property.id] && "text-muted-foreground"
                                    )}
                                  >
                                    <CalendarIcon className="mr-2 h-4 w-4" />
                                    {selectedValues[property.id] ? format(new Date(selectedValues[property.id]), 'PPP') : <span>日付を選択</span>}
                                  </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                  <Calendar
                                    mode="single"
                                    selected={selectedValues[property.id] ? new Date(selectedValues[property.id]) : undefined}
                                    onSelect={(date) => handlePropertyChange(property.id, date ? date.toISOString() : '')}
                                    initialFocus
                                  />
                                </PopoverContent>
                              </Popover>
                            ) : property.type === 'multi_select' ? (
                              <Select
                                value={selectedValues[property.id]}
                                onValueChange={(value) => handlePropertyChange(property.id, value)}
                              >
                                <SelectTrigger>
                                  <SelectValue placeholder={`${property.name}を選択`} />
                                </SelectTrigger>
                                <SelectContent>
                                  {property.options?.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            ) : property.type === 'relation_select' ? (
                              <Select
                                value={selectedValues[property.id]}
                                onValueChange={(value) => handlePropertyChange(property.id, value)}
                              >
                                <SelectTrigger className="w-full">
                                  <SelectValue placeholder={`関連ページを選択`} />
                                </SelectTrigger>
                                <SelectContent className={cn(
                                  "max-h-[200px]",
                                  "overflow-y-auto"
                                )}>
                                  {property.options?.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            ) : (
                              <Select
                                value={selectedValues[property.id]}
                                onValueChange={(value) => handlePropertyChange(property.id, value)}
                              >
                                <SelectTrigger className="w-full">
                                  <SelectValue placeholder={`${property.name}を選択`} />
                                </SelectTrigger>
                                <SelectContent className={cn(
                                  "max-h-[200px]",
                                  "overflow-y-auto"
                                )}>
                                  {property.options?.map(option => (
                                    <SelectItem key={option.value} value={option.value}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </ScrollArea>
  )
}

