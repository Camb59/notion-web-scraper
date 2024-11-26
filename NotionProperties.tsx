'use client'

import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useState } from 'react';

interface NotionPropertiesProps {
  properties: Record<string, string>;
  onPropertyChange: (key: string, value: string) => void;
  notionDatabaseProperties: Record<string, string>;
}

export default function NotionProperties({
  properties,
  onPropertyChange,
  notionDatabaseProperties,
}: NotionPropertiesProps) {
  //const [propertyOrder, setPropertyOrder] = useState(Object.keys(properties));

  //const onDragEnd = (result) => {
  //  if (!result.destination) return;
  //  const items = Array.from(propertyOrder);
  //  const [reorderedItem] = items.splice(result.source.index, 1);
  //  items.splice(result.destination.index, 0, reorderedItem);
  //  setPropertyOrder(items);
  //  onOrderChange(items);
  //};

  return (
    <ScrollArea className="h-[600px]">
      <div className="space-y-4 pr-4">
        {Object.entries(properties).map(([key, value]) => (
          <Card key={key}>
            <CardContent className="pt-4">
              <div className="space-y-2">
                <Label htmlFor={key}>{key}</Label>
                <Select
                  defaultValue={value}
                  onValueChange={(newValue) => onPropertyChange(key, newValue)}
                >
                  <SelectTrigger id={key}>
                    <SelectValue placeholder="プロパティタイプを選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(notionDatabaseProperties).map(([propName, propType]) => (
                      <SelectItem key={propName} value={propType}>
                        {propName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}

