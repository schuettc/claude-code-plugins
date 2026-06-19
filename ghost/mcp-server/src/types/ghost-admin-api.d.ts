declare module "@tryghost/admin-api" {
  interface BrowseParams {
    limit?: number | "all";
    page?: number;
    filter?: string;
    order?: string;
    include?: string;
    fields?: string;
    formats?: string[];
  }
  interface Resource {
    browse(params?: BrowseParams): Promise<any[]>;
    read(data: Record<string, any>, options?: Record<string, any>): Promise<any>;
    add(data: Record<string, any>, options?: Record<string, any>): Promise<any>;
    edit(data: Record<string, any>, options?: Record<string, any>): Promise<any>;
  }
  interface Images {
    upload(data: { file: string; ref?: string }): Promise<{ url: string }>;
  }
  interface Site {
    read(): Promise<{ title: string; url: string; version: string }>;
  }
  export default class GhostAdminAPI {
    constructor(options: { url: string; key: string; version: string });
    posts: Resource;
    pages: Resource;
    tags: Resource;
    images: Images;
    site: Site;
  }
}
